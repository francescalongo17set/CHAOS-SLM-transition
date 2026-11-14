"""FT-P0 step 1: recompute the chapter-02 facts on the real train split. Read-only; prints a table, exits 1 on any difference.

  python orchestrator/fine-tuning/common/audit_train.py
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
from orchestrator.baselines.common import data                       # noqa: E402

rows = data.load_split("train")
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
    "needs_clar rows (metadata, not trained on in v2)": sum(bool(r.labels.get("missing_info")) for r in rows),
}
bund = C(r.support.get("bundle_id") for r in rows)
facts["bundle groups"] = len(bund)
facts["bundle size dist"] = dict(sorted(C(bund.values()).items()))
facts["pair_id links (rows with pair_id)"] = sum(r.pair_id is not None for r in rows)
facts["distinct pair_ids"] = len({r.pair_id for r in rows if r.pair_id is not None})
for k, v in facts.items():
    print(f"{k}: {v}")
