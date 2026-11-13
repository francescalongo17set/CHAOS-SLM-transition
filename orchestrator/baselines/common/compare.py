"""Cross-pipeline comparison.md generator (chapter 05). Tolerates missing pipelines.

Usage: python -m common.compare --runs kev=path/metrics_test.json laya=... nimble=... \
           [--dropped nimble="reason"] --out reports/comparison.md
"""
import argparse
import json
from pathlib import Path

PIPELINES = ("kev", "laya", "nimble")


def _f(x, d=3):
    return "n/a" if x is None else (f"{x:.{d}f}" if isinstance(x, float) else str(x))


def build(runs, dropped=None):
    """runs: {label: metrics dict}. dropped: {pipeline: reason}."""
    dropped = dropped or {}
    L = ["# Comparison", "", "Differences within about 2 points on 593 test rows are noise (chapter 05); no winner is declared.", ""]
    if not runs:
        L += ["No runs available yet.", ""]
    else:
        labels = list(runs)
        gpus = {l: runs[l].get("run", {}).get("device") for l in labels}
        modes = {l: runs[l].get("run", {}).get("latency_mode") for l in labels}
        L += ["| metric | " + " | ".join(labels) + " |", "|---|" + "---|" * len(labels)]
        rows = [
            ("scope_check accuracy", lambda m: m["scope_check"]["accuracy"]),
            ("scope_check macro-F1", lambda m: m["scope_check"]["macro_f1"]),
            ("feature accuracy", lambda m: m["feature_classification"]["accuracy"]),
            ("feature macro-F1", lambda m: m["feature_classification"]["macro_f1"]),
            ("complexity accuracy", lambda m: m["complexity_estimation"]["accuracy"]),
            ("complexity macro-F1", lambda m: m["complexity_estimation"]["macro_f1"]),
            ("route accuracy (tau=None)", lambda m: m["route"]["accuracy"]),
            ("route macro-F1", lambda m: m["route"]["macro_f1"]),
            ("refuse recall (all)", lambda m: m["refuse_recall"]["all"]["recall"]),
            ("refuse recall (safety leak)", lambda m: m["refuse_recall"]["safety_leak"]["recall"]),
            ("input_tokens_native (mean)", lambda m: m["tokens"]["input_native"].get("mean")),
            ("input_tokens_ref (mean)", lambda m: m["tokens"]["input_ref"].get("mean")),
            ("latency p50 ms", lambda m: m["latency_ms"].get("p50")),
            ("latency p95 ms", lambda m: m["latency_ms"].get("p95")),
            ("error rows", lambda m: m["n_error_rows"]),
        ]
        for name, fn in rows:
            vals = []
            for l in labels:
                try:
                    vals.append(_f(fn(runs[l])))
                except (KeyError, TypeError):
                    vals.append("n/a")
            L.append(f"| {name} | " + " | ".join(vals) + " |")
        L += ["", "## Comparability flags", ""]
        L.append(f"- GPUs: {gpus}" + ("  **DIFFERENT: latency is not comparable across these runs.**" if len({g for g in gpus.values()}) > 1 else ""))
        L.append(f"- Latency modes: {modes}" + ("  **DIFFERENT: not comparable.**" if len({g for g in modes.values()}) > 1 else ""))
        hosted = [l for l in labels if modes[l] == "http_hosted"]
        if hosted:
            L.append(f"- Hosted runs (include network time, **not comparable** with local): {hosted}")
        L.append("")
    L += ["## Missing or dropped pipelines", ""]
    present = {l.split("-")[0] for l in runs}
    absent = [p for p in PIPELINES if p not in present]
    if not absent:
        L.append("None.")
    for p in absent:
        L.append(f"- **{p}**: " + (f"dropped, {dropped[p]}" if p in dropped else "no run provided yet"))
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="*", default=[])
    ap.add_argument("--dropped", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    runs = {kv.split("=", 1)[0]: json.loads(Path(kv.split("=", 1)[1]).read_text()) for kv in a.runs}
    dropped = dict(kv.split("=", 1) for kv in a.dropped)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(build(runs, dropped), encoding="utf-8")


if __name__ == "__main__":
    main()
