"""Pure-python evaluation: data loading, gold routes, metrics, threshold sweep, knee. No GPU, no numpy."""
import csv
import hashlib
import json
from dataclasses import replace

from orch.router import COST, Thresholds, route

LABELS = {"scope": {"in_scope", "out_of_scope"},
          "complexity": {"lightweight", "agentic", "n/a"},   # n/a = out of scope or unsafe (never reaches the choice)
          "safety": {"safe", "unsafe"}}


def sha256(path) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_rows(path) -> list:
    """Read .csv (hand-edited gold, utf-8 with BOM from Excel is fine) or .jsonl, and reject typos in labels."""
    if str(path).endswith(".csv"):
        rows = list(csv.DictReader(open(path, encoding="utf-8-sig", newline="")))
    else:
        rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    for r in rows:
        for k, ok in LABELS.items():
            r[k] = (r.get(k) or "").strip()
            if r[k] not in ok:
                raise ValueError(f"{path}: row {r.get('id')}: {k}={r[k]!r}, expected one of {sorted(ok)}")
    return rows


def gold_route(r) -> str:
    if r["safety"] == "unsafe" or r["scope"] == "out_of_scope":
        return "stop"
    if r["complexity"] == "n/a":
        raise ValueError(f"row {r.get('id')}: in-scope safe row needs complexity lightweight|agentic")
    return "agentic" if r["complexity"] == "agentic" else "lightweight"


def predict(d, th: Thresholds) -> dict:
    """Thresholded per-decision labels + the route, from one query's three Decisions."""
    rt = route(d, th)
    return {"safety": "unsafe" if d["safety"].prob("unsafe") >= th.unsafe else "safe",
            "scope": "out_of_scope" if d["scope"].prob("out_of_scope") >= th.out_of_scope else "in_scope",
            "complexity": "lightweight" if d["complexity"].prob("lightweight") >= th.lightweight else "agentic",
            "route": rt.route}


def _rate(num, den):
    return num / den if den else float("nan")


def metrics(rows, decs, th: Thresholds, agentic_cost=COST["agentic"]) -> dict:
    """decs: {row id: {'safety'|'scope'|'complexity': Decision}}."""
    cost = {**COST, "agentic": agentic_cost}
    P = [(r, predict(decs[r["id"]], th), gold_route(r)) for r in rows]
    cx = [(r, p) for r, p, _ in P if r["complexity"] != "n/a"]
    light = [(p, g) for _, p, g in P if g == "lightweight"]
    hard = [(p, g) for _, p, g in P if g == "agentic"]
    unsafe = [p for r, p, _ in P if r["safety"] == "unsafe"]
    normal = [p for r, p, g in P if g != "stop"]
    stop = [p for _, p, g in P if g == "stop"]
    return {
        "n": len(P),
        "acc_safety": _rate(sum(p["safety"] == r["safety"] for r, p, _ in P), len(P)),
        "acc_scope": _rate(sum(p["scope"] == r["scope"] for r, p, _ in P), len(P)),
        "acc_complexity": _rate(sum(p["complexity"] == r["complexity"] for r, p in cx), len(cx)),
        "acc_route": _rate(sum(p["route"] == g for _, p, g in P), len(P)),
        "false_escalation": _rate(sum(p["route"] == "agentic" for p, _ in light), len(light)),   # easy -> agentic: wasted cost
        "false_lightweight": _rate(sum(p["route"] == "lightweight" for p, _ in hard), len(hard)),  # hard -> lightweight: quality risk
        "safety_recall": _rate(sum(p["route"] == "stop" for p in unsafe), len(unsafe)),           # unsafe actually stopped
        "safety_recall_decision": _rate(sum(p["safety"] == "unsafe" for p in unsafe), len(unsafe)),
        "false_block": _rate(sum(p["route"] == "stop" for p in normal), len(normal)),             # fine query wrongly stopped
        "stop_recall": _rate(sum(p["route"] == "stop" for p in stop), len(stop)),
        "agentic_share": _rate(sum(p["route"] == "agentic" for _, p, _ in P), len(P)),
        "cost": _rate(sum(cost[p["route"]] for _, p, _ in P), len(P)),                           # mean cost units per query
    }


def sweep(rows, decs, th: Thresholds, ts, agentic_cost=COST["agentic"]) -> list:
    return [{"t_lightweight": t, **metrics(rows, decs, replace(th, lightweight=t), agentic_cost)} for t in ts]


def knee(points, x="cost", y="acc_route") -> int:
    """Index of the point farthest above the straight line between the cheapest and the dearest point."""
    # only points nobody beats on both axes (cheaper and at least as accurate); otherwise a curve that
    # gets WORSE as cost rises produces a meaningless "knee"
    order = sorted(range(len(points)), key=lambda i: (points[i][x], -points[i][y]))
    pts, best_y = [], float("-inf")
    for i in order:
        if points[i][y] > best_y + 1e-12:
            pts.append(i)
            best_y = points[i][y]
    (x0, y0), (x1, y1) = [(points[i][x], points[i][y]) for i in (pts[0], pts[-1])]
    if x1 == x0:
        return pts[0]
    best, best_d = pts[0], float("-inf")
    for i in pts:
        d = (points[i][y] - y0) - (y1 - y0) / (x1 - x0) * (points[i][x] - x0)
        if d > best_d + 1e-12:  # strict: on ties keep the cheaper point
            best, best_d = i, d
    return best


def tune_stops(rows, decs, th: Thresholds, target_recall=0.9, grid=(0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)) -> Thresholds:
    """Pick the two 'stop' thresholds on tuning data: best route accuracy among settings that still catch at least
    target_recall of unsafe queries (if none reach it, the best recall wins). The complexity threshold is left alone."""
    best, best_key = th, None
    for tu in grid:
        for to in grid:
            t = replace(th, unsafe=tu, out_of_scope=to)
            m = metrics(rows, decs, t)
            rec = m["safety_recall"] if m["safety_recall"] == m["safety_recall"] else 1.0  # no unsafe rows: nan -> ok
            key = (rec >= target_recall, rec if rec < target_recall else 0, m["acc_route"])
            if best_key is None or key > best_key:
                best, best_key = t, key
    return best


def plot_sweep(points, k, path):
    """Left: cost vs route accuracy with the knee. Right: the two error rates against the threshold."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.2))
    a.plot([p["cost"] for p in points], [p["acc_route"] for p in points], "o-", label="model (threshold sweep)")
    a.plot(points[k]["cost"], points[k]["acc_route"], "r*", ms=16, label=f"knee t={points[k]['t_lightweight']:.2f}")
    a.set(xlabel="mean cost per query (lightweight=1, agentic=5)", ylabel="route accuracy", title="Cost vs accuracy")
    a.legend(fontsize=8)
    t = [p["t_lightweight"] for p in points]
    b.plot(t, [p["false_escalation"] for p in points], label="false escalation (easy -> agentic)")
    b.plot(t, [p["false_lightweight"] for p in points], label="false lightweight (hard -> lightweight)")
    b.axvline(points[k]["t_lightweight"], color="r", ls="--")
    b.set(xlabel="lightweight confidence threshold", ylabel="rate", title="Error trade-off")
    b.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
