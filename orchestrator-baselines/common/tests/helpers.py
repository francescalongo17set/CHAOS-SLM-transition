"""Test helpers: perfect (gold) and seeded-random logs."""
import random

from common import data
from common.logs import build_record
from common.questions import CANONICAL_OPTIONS, QuestionConfig

META = {"run_id": "test", "pipeline": "kev", "model_id": "m", "model_revision": "r", "split": "test"}


def _ans(options, label, rng=None, perfect=True):
    if perfect:
        probs = {o: (1.0 if o == label else 0.0) for o in options}
    else:
        w = [rng.random() + 1e-3 for _ in options]
        t = sum(w)
        probs = {o: x / t for o, x in zip(options, w)}
        label = max(probs, key=probs.get)
    return {"label": label, "probs": probs, "option_order": list(options)}


def make_log(split, perfect=True, seed=0, gold_slots=True):
    q = QuestionConfig()
    rng = random.Random(seed)
    meta = dict(META, split=split)
    out = []
    for row in data.load_split(split):
        lab = row.labels
        if perfect:
            feat = lab["feature"]
            ans = {
                "scope_check": _ans(CANONICAL_OPTIONS["scope_check"], lab["scope_check"]),
                "feature_classification": _ans(CANONICAL_OPTIONS["feature_classification"], feat),
                "complexity_estimation": _ans(CANONICAL_OPTIONS["complexity_estimation"], lab.get("complexity", "simple")),
                "slots": {s: _ans(CANONICAL_OPTIONS["slots"], row.support["slot_status"].get(s, "present"))
                          for s in q.slots_for_feature(feat)},
            }
            # C-29: date_reference is not asked. On rows where it is the only missing slot, the oracle
            # flags the first asked slot as missing so needs_clarification still equals gold.
            if lab.get("missing_info") and all(v["label"] == "present" for v in ans["slots"].values()):
                first = next(iter(ans["slots"]))
                ans["slots"][first] = _ans(CANONICAL_OPTIONS["slots"], "missing")
            # insurer may lack gold status on 140 rows (C-28): perfect log marks it present, which keeps
            # needs_clarification equal to gold because those rows have another non-present slot.
        else:
            ans = {k: _ans(CANONICAL_OPTIONS[k], None, rng, False) for k in
                   ("scope_check", "feature_classification", "complexity_estimation")}
            feat = ans["feature_classification"]["label"]
            ans["slots"] = {s: _ans(CANONICAL_OPTIONS["slots"], None, rng, False) for s in q.slots_for_feature(feat)}
        rec = build_record(row, meta, ans, latency_ms=100.0 + rng.random() * 50)
        rec["tokens"] = {"input_native": 500, "input_ref": 480, "output_native": None, "usage_reported": None}
        out.append(rec)
    return out
