"""Test helpers: perfect (gold) and seeded-random logs (v2: three answers per row)."""
import random

from orchestrator.baselines.common import data
from orchestrator.baselines.common.logs import build_record
from orchestrator.baselines.common.questions import CANONICAL_OPTIONS

META = {"run_id": "test", "pipeline": "kev", "model_id": "m", "model_revision": "r", "split": "test"}
CORE = ("scope_check", "feature_classification", "complexity_estimation")


def _ans(options, label, rng=None, perfect=True):
    if perfect:
        probs = {o: (1.0 if o == label else 0.0) for o in options}
    else:
        w = [rng.random() + 1e-3 for _ in options]
        t = sum(w)
        probs = {o: x / t for o, x in zip(options, w)}
        label = max(probs, key=probs.get)
    return {"label": label, "probs": probs, "option_order": list(options)}


def make_log(split, perfect=True, seed=0):
    rng = random.Random(seed)
    meta = dict(META, split=split)
    out = []
    for row in data.load_split(split):
        lab = row.labels
        if perfect:
            gold = {"scope_check": lab["scope_check"], "feature_classification": lab["feature"],
                    "complexity_estimation": lab.get("complexity", "simple")}
            ans = {k: _ans(CANONICAL_OPTIONS[k], gold[k]) for k in CORE}
        else:
            ans = {k: _ans(CANONICAL_OPTIONS[k], None, rng, False) for k in CORE}
        rec = build_record(row, meta, ans, latency_ms=100.0 + rng.random() * 50)
        rec["tokens"] = {"input_native": 500, "input_ref": 480, "output_native": None, "usage_reported": None}
        out.append(rec)
    return out
