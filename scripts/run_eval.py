"""Step 5: score calibration + test + gold with the fine-tuned Laya model, tune thresholds on CALIBRATION only,
report the fixed thresholds on TEST and GOLD, write the decision log and the cost-vs-accuracy plot, log to MLflow.

Test and gold never choose anything: stop thresholds and the complexity knee come from the calibration split.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so `orch` imports without install

from dataclasses import replace

from orch.backends import BASE_MODEL, LayaBackend
from orch.decision import QUESTIONS, Decision
from orch.evalkit import knee, load_rows, metrics, plot_sweep, sha256, sweep, tune_stops
from orch.router import COST, Thresholds, log_record, route

TS = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.97, 0.98, 0.99, 0.995]
SHOW = ["acc_safety", "acc_scope", "acc_complexity", "acc_route", "false_escalation", "false_lightweight", "safety_recall", "false_block", "cost"]


def score(backend, rows, cache_path):
    """Ask the three questions per row; append each result to a cache so a killed run resumes. Stale if the query text changed."""
    done = {}
    if os.path.exists(cache_path):
        for line in open(cache_path, encoding="utf-8"):
            r = json.loads(line)
            done[r["id"]] = r
    key = lambda r: hashlib.sha1(r["query"].encode()).hexdigest()[:10]
    with open(cache_path, "a", encoding="utf-8") as f:
        for r in rows:
            if r["id"] in done and done[r["id"]]["q"] == key(r):
                continue
            t0 = time.perf_counter()
            d = {k: backend.decide(r["query"], q, ch) for k, (q, ch) in QUESTIONS.items()}
            rec = {"id": r["id"], "q": key(r), "latency_ms": (time.perf_counter() - t0) * 1000,
                   "decisions": {k: v.to_dict() for k, v in d.items()}}
            f.write(json.dumps(rec) + "\n")
            f.flush()
            done[r["id"]] = rec
    return {r["id"]: {k: Decision.from_dict(v) for k, v in done[r["id"]]["decisions"].items()} for r in rows}, \
           [done[r["id"]]["latency_ms"] for r in rows]


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))]


def fmt(m):
    return "  ".join(f"{k.replace('acc_', '')}={m[k]:.3f}" for k in SHOW)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=BASE_MODEL, help="the fine-tuned Laya folder (or the untouched base checkpoint for a zero-shot reference)")
    ap.add_argument("--calib", default="data/v2/calib.jsonl")
    ap.add_argument("--test", default="data/v2/test.jsonl")
    ap.add_argument("--gold", default="data/v2/gold.csv")
    ap.add_argument("--agentic-cost", type=float, default=COST["agentic"], help="cost of an agentic run relative to lightweight=1")
    ap.add_argument("--target-recall", type=float, default=0.9, help="minimum share of unsafe queries the stop thresholds must catch on calibration")
    ap.add_argument("--out", default=f"runs/{time.strftime('%Y%m%d-%H%M%S')}")
    ap.add_argument("--mlflow-uri", default=os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"),
                    help="default: $MLFLOW_TRACKING_URI, else a local SQLite file. (MLflow now blocks the plain-folder store unless MLFLOW_ALLOW_FILE_STORE=true.)")
    ap.add_argument("--no-mlflow", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    paths = {"calib": a.calib, "test": a.test, "gold": a.gold}
    data = {k: load_rows(p) for k, p in paths.items()}
    hashes = {f"{k}_sha256": sha256(p) for k, p in paths.items()}
    backend = LayaBackend(a.model)
    scored, lat = {}, []
    for split, rows in data.items():
        scored[split], l = score(backend, rows, f"{a.out}/scores_{split}.jsonl")
        lat += l

    # 1) stop thresholds, then 2) complexity threshold sweep with the stops fixed, both on calibration only
    th0 = tune_stops(data["calib"], scored["calib"], Thresholds(lightweight=0.5), a.target_recall)
    curve = sweep(data["calib"], scored["calib"], th0, TS, a.agentic_cost)
    k = knee(curve)
    th = replace(th0, lightweight=curve[k]["t_lightweight"])
    res = {"model": backend.name, "model_version": backend.version, "thresholds": th.__dict__,
           **{s: metrics(data[s], scored[s], th, a.agentic_cost) for s in data},
           "latency_ms_p50": pct(lat, 0.5), "latency_ms_p95": pct(lat, 0.95)}
    with open(f"{a.out}/sweep_calib.csv", "w", newline="") as f:
        w = csv.DictWriter(f, curve[0].keys())
        w.writeheader()
        w.writerows(curve)
    with open(f"{a.out}/decision_log.jsonl", "w", encoding="utf-8") as f:  # one line per routed query, final thresholds
        for split, rows in data.items():
            for r in rows:
                d = scored[split][r["id"]]
                f.write(json.dumps({"split": split, "id": r["id"], **log_record(r["query"], d, th, route(d, th), backend)}, ensure_ascii=False) + "\n")
    plot_sweep(curve, k, f"{a.out}/cost_vs_accuracy.png")
    json.dump(res, open(f"{a.out}/metrics.json", "w"), indent=1)

    print(f"\n{backend.name}  thresholds: {th}   p50={res['latency_ms_p50']:.0f}ms  p95={res['latency_ms_p95']:.0f}ms")
    for s in data:
        print(f"  {s:5}", fmt(res[s]))

    if not a.no_mlflow:
        try:
            import mlflow
        except ImportError:
            print("mlflow not installed, skipping tracking")
        else:
            mlflow.set_tracking_uri(a.mlflow_uri)
            mlflow.set_experiment("orchestrator-laya")
            with mlflow.start_run(run_name=backend.name):
                mlflow.log_params({"model": backend.name, "model_version": backend.version, "agentic_cost": a.agentic_cost,
                                   "target_recall": a.target_recall, **{f"t_{k}": v for k, v in th.__dict__.items()}, **hashes,
                                   **{f"n_{s}": len(r) for s, r in data.items()}})
                mlflow.log_metrics({f"{s}_{k}": v for s in data for k, v in res[s].items() if k != "n" and not math.isnan(v)}
                                   | {"latency_ms_p50": res["latency_ms_p50"], "latency_ms_p95": res["latency_ms_p95"]})
                for f in ("sweep_calib.csv", "decision_log.jsonl", "cost_vs_accuracy.png", "metrics.json"):
                    mlflow.log_artifact(f"{a.out}/{f}")
    print(f"\nwrote {a.out}/")
