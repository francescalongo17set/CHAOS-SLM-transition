"""FT-P0 step 1: recompute the chapter-02 facts on the real train split. Read-only; prints a table, exits 1 on any difference.

  python orchestrator/fine-tuning/common/audit_train.py
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
from orchestrator.baselines.common import data                       # noqa: E402
from orchestrator.baselines.common.questions import QuestionConfig    # noqa: E402

rows = data.load_split("train")
q = QuestionConfig()
C = lambda it: dict(Counter(it))
facts = {
    "n_rows": len(rows),
    "routes": C(r.support["expected_route"] for r in rows),
    "scope": C(r.labels["scope_check"] for r in rows),
    "feature": C(r.labels["feature"] for r in rows),
    "complexity (in_scope)": C(r.labels["complexity"] for r in rows if "complexity" in r.labels),
    "safety_leak true": sum(bool(r.support["safety_leak"]) for r in rows),
    "history 0 / 2 / 3-6 turns": (sum(len(r.model_input.history) == 0 for r in rows),
                                  sum(len(r.model_input.history) == 2 for r in rows),
                                  sum(3 <= len(r.model_input.history) <= 6 for r in rows)),
    "history other lengths": C(len(r.model_input.history) for r in rows if len(r.model_input.history) not in (0, 2, 3, 4, 5, 6)),
    "slot_status (all rows)": C(s for r in rows for s in r.support["slot_status"].values()),
    "gold needs_clar == any slot not present": all(bool(r.labels.get("missing_info")) == any(s != "present" for s in r.support["slot_status"].values()) for r in rows),
    "needs_clar true": sum(bool(r.labels.get("missing_info")) for r in rows),
}
bund = C(r.support.get("bundle_id") for r in rows)
facts["bundle groups"] = len(bund)
facts["bundle size dist"] = dict(sorted(C(bund.values()).items()))
facts["pair_id links (rows with pair_id)"] = sum(r.pair_id is not None for r in rows)
facts["distinct pair_ids"] = len({r.pair_id for r in rows if r.pair_id is not None})
# slot rules
skip_insurer = C(r.labels["feature"] for r in rows if "insurer" in q.slots_for_feature(r.labels["feature"]) and "insurer" not in r.support["slot_status"])
facts["rows whose by_feature slot is absent from slot_status"] = skip_insurer
absent = C((r.labels["feature"], s) for r in rows for s in q.slots_for_feature(r.labels["feature"]) if s not in r.support["slot_status"])
facts["absent (feature, slot)"] = {f"{k[0]}:{k[1]}": v for k, v in absent.items()}
facts["rows with date_reference in slot_status"] = sum("date_reference" in r.support["slot_status"] for r in rows)
facts["slot_status keys not in by_feature (excluding date_reference)"] = C(
    s for r in rows for s in r.support["slot_status"] if s not in q.slots_for_feature(r.labels["feature"]) and s != "date_reference")
facts["none-feature rows with slots"] = sum(bool(q.slots_for_feature("none")) for r in rows if r.labels["feature"] == "none")
for k, v in facts.items():
    print(f"{k}: {v}")
