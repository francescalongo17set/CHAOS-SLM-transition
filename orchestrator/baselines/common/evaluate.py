"""Evaluation (chapter 05). Reads a validated prediction log + ground truth, computes every number.
Pure standard library. Pipelines never compute metrics themselves (rule 7)."""
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from . import data
from .dispatcher import ROUTES, dispatch
from .logs import read_log, validate_log
from .questions import CANONICAL_OPTIONS


# ---------- generic metrics ----------
def prf(gold, pred, labels):
    """Per-class precision/recall/F1/support + accuracy + macro-F1 (over labels with gold support)."""
    n = len(gold)
    per = {}
    for c in labels:
        tp = sum(1 for g, p in zip(gold, pred) if g == c and p == c)
        fp = sum(1 for g, p in zip(gold, pred) if g != c and p == c)
        fn = sum(1 for g, p in zip(gold, pred) if g == c and p != c)
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
        per[c] = {"precision": pr, "recall": rc, "f1": f1, "support": tp + fn}
    scored = [c for c in labels if per[c]["support"] > 0]
    acc = sum(1 for g, p in zip(gold, pred) if g == p) / n if n else float("nan")
    macro = sum(per[c]["f1"] for c in scored) / len(scored) if scored else float("nan")
    return {"n": n, "accuracy": acc, "macro_f1": macro, "per_class": per}


def confusion(gold, pred, labels):
    cols = list(labels) + ["<error>"]
    m = {g: Counter() for g in labels}
    for g, p in zip(gold, pred):
        m[g][p if p in labels else "<error>"] += 1
    return cols, m


def ece_brier(items, options, bins=10):
    """items: list of (probs dict, gold label). ECE on p_max with equal-width bins; multiclass Brier."""
    if not items:
        return {"n": 0, "ece": None, "brier": None}
    b = [[0, 0.0, 0] for _ in range(bins)]  # count, sum conf, sum correct
    brier = 0.0
    for probs, gold in items:
        top = max(options, key=lambda o: probs[o])
        conf = probs[top]
        i = min(int(conf * bins), bins - 1)
        b[i][0] += 1
        b[i][1] += conf
        b[i][2] += 1 if top == gold else 0
        brier += sum((probs[o] - (1.0 if o == gold else 0.0)) ** 2 for o in options)
    n = len(items)
    ece = sum(c / n * abs(sc / c - sk / c) for c, sc, sk in b if c)
    return {"n": n, "ece": ece, "brier": brier / n}


def dist(xs):
    xs = sorted(xs)
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "mean": statistics.fmean(xs), "median": statistics.median(xs),
            "p95": xs[int(0.95 * (len(xs) - 1))], "total": sum(xs)}


# ---------- main ----------
def _pred(rec, key):
    a = rec.get("answers")
    return a[key]["label"] if a and key in a else None


def evaluate(log_path, split, data_dir=None, run_json=None, out_dir=None):
    errs = validate_log(log_path, split, data_dir)
    if errs:
        raise ValueError(f"log not accepted ({len(errs)} problems), first: {errs[:5]}")
    rows = {r.query_id: r for r in data.load_split(split, data_dir)}
    recs = {r["query_id"]: r for r in read_log(log_path)}
    M = {"split": split, "n_rows": len(rows)}
    n_err = sum(1 for r in recs.values() if r["error"] is not None)
    M["n_error_rows"] = n_err
    M["n_truncated"] = sum(1 for r in recs.values() if r.get("truncated"))
    M["pipeline"] = next(iter(recs.values()))["pipeline"] if recs else None
    M["model_id"] = next(iter(recs.values()))["model_id"] if recs else None
    M["model_revision"] = next(iter(recs.values()))["model_revision"] if recs else None

    ids = sorted(rows)
    ins = [q for q in ids if rows[q].labels["scope_check"] == "in_scope"]

    def collect(qs, getgold, key):
        return [getgold(rows[q]) for q in qs], [_pred(recs[q], key) for q in qs]

    cm = {}
    for name, qs, gfn, key, labels in [
        ("scope_check", ids, lambda r: r.labels["scope_check"], "scope_check", CANONICAL_OPTIONS["scope_check"]),
        ("feature_classification", ids, lambda r: r.labels["feature"], "feature_classification",
         CANONICAL_OPTIONS["feature_classification"]),
        ("complexity_estimation", ins, lambda r: r.labels["complexity"], "complexity_estimation",
         CANONICAL_OPTIONS["complexity_estimation"]),
    ]:
        g, p = collect(qs, gfn, key)
        M[name] = prf(g, p, labels)
        cm[name] = confusion(g, p, labels)

    gold_nc = [bool(rows[q].labels["missing_info"]) for q in ins]
    pred_nc = [(recs[q]["needs_clarification"] if recs[q]["error"] is None else None) for q in ins]
    M["needs_clarification"] = prf(gold_nc, pred_nc, [True, False])
    M["needs_clarification"]["positive_class"] = M["needs_clarification"]["per_class"][True]
    M["needs_clarification"]["per_class"] = {str(k): v for k, v in M["needs_clarification"]["per_class"].items()}
    cm["needs_clarification"] = confusion([str(x) for x in gold_nc], [str(x) for x in pred_nc], ["True", "False"])

    # end-to-end route (tau=None) and attribution
    pred_route, attrib = {}, Counter()
    for q in ids:
        r = recs[q]
        if r["error"] is not None:
            pred_route[q] = None
            continue
        a = r["answers"]
        pred_route[q] = dispatch(a["scope_check"]["label"], a["feature_classification"]["label"],
                                 a["complexity_estimation"]["label"], r["needs_clarification"])
    gold_route = [rows[q].support["expected_route"] for q in ids]
    M["route"] = prf(gold_route, [pred_route[q] for q in ids], list(ROUTES))
    cm["route"] = confusion(gold_route, [pred_route[q] for q in ids], list(ROUTES))
    for q in ids:
        if pred_route[q] == rows[q].support["expected_route"]:
            continue
        r, lab = recs[q], rows[q].labels
        if r["error"] is not None:
            attrib["call error"] += 1
            continue
        a = r["answers"]
        first = "none (fields right, route wrong)"
        if a["scope_check"]["label"] != lab["scope_check"]:
            first = "scope_check"
        elif a["feature_classification"]["label"] != lab["feature"]:
            first = "feature_classification"
        elif lab["scope_check"] == "in_scope" and r["needs_clarification"] != bool(lab["missing_info"]):
            first = "needs_clarification"
        elif lab["scope_check"] == "in_scope" and a["complexity_estimation"]["label"] != lab["complexity"]:
            first = "complexity_estimation"
        attrib[first] += 1
    M["route_attribution"] = dict(attrib)

    # dispatcher oracle (sanity line)
    from .dispatcher import dispatch_gold
    M["dispatcher_oracle"] = {"n": len(ids), "matches": sum(
        1 for q in ids if dispatch_gold(rows[q]) == rows[q].support["expected_route"])}

    # refuse recall slices
    def refuse_recall(qs):
        g = [q for q in qs if rows[q].support["expected_route"] == "refuse"]
        hit = sum(1 for q in g if pred_route[q] == "refuse")
        return {"n_gold_refuse": len(g), "recall": hit / len(g) if g else None}
    leak = [q for q in ids if rows[q].support.get("safety_leak")]
    by_type = defaultdict(list)
    for q in leak:
        by_type[rows[q].support["leak_type"]].append(q)
    M["refuse_recall"] = {
        "all": refuse_recall(ids), "safety_leak": refuse_recall(leak),
        "non_leak": refuse_recall([q for q in ids if q not in set(leak)]),
        "by_leak_type": {t: refuse_recall(v) for t, v in sorted(by_type.items())},
    }

    # calibration, as shipped (no refit), error rows excluded
    cal = {}
    ok = lambda q: recs[q]["error"] is None
    for name, qs, gfn in [
        ("scope_check", ids, lambda r: r.labels["scope_check"]),
        ("feature_classification", ids, lambda r: r.labels["feature"]),
        ("complexity_estimation", ins, lambda r: r.labels["complexity"]),
    ]:
        items = [(recs[q]["answers"][name]["probs"], gfn(rows[q])) for q in qs if ok(q)]
        cal[name] = ece_brier(items, CANONICAL_OPTIONS[name])
    sl = []
    for q in ids:
        if not ok(q):
            continue
        for s, ans in recs[q]["answers"]["slots"].items():
            g = rows[q].support["slot_status"].get(s)
            if g is not None:
                sl.append((ans["probs"], g))
    cal["slots (pooled, where gold slot status exists)"] = ece_brier(sl, CANONICAL_OPTIONS["slots"])
    M["calibration"] = cal

    # tokens, latency
    good = [recs[q] for q in ids if recs[q]["error"] is None]
    M["tokens"] = {k: dist([r["tokens"][k] for r in good if r["tokens"].get(k) is not None])
                   for k in ("input_native", "input_ref", "output_native")}
    lat = [r["latency_ms"] for r in good if not r["is_warmup"]]
    M["latency_ms"] = dict(dist(lat), p50=statistics.median(lat) if lat else None,
                           n_warmup_excluded=sum(1 for r in good if r["is_warmup"]))
    if run_json and Path(run_json).exists():
        M["run"] = json.loads(Path(run_json).read_text())

    if out_dir:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        for name, (cols, m) in cm.items():
            with open(out / f"confusion_{split}_{name}.csv", "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["gold\\pred"] + cols)
                for g, c in m.items():
                    w.writerow([g] + [c[x] for x in cols])
        (out / f"metrics_{split}.json").write_text(json.dumps(M, indent=1, sort_keys=True, default=str))
    return M
