"""Training record == evaluation request, as upstream renders them. Needs upstream kev importable (set KEV_SRC to its clone,
or run inside the notebook venv); skipped otherwise. No GPU."""
import json
import os
import sys
from pathlib import Path

import pytest

if os.environ.get("KEV_SRC"):
    sys.path.insert(0, os.environ["KEV_SRC"])
pytest.importorskip("kev.api")
pytest.importorskip("datasets")

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT / "fine-tuning" / "common"))
from kev.api import to_record                                   # noqa: E402
from kev.data import api_request, load_records                  # noqa: E402
import build_data                                               # noqa: E402
from orchestrator.baselines.common import data                  # noqa: E402
from orchestrator.baselines.common.questions import QuestionConfig  # noqa: E402
from orchestrator.baselines.kev.adapter import build_request    # noqa: E402

QC = QuestionConfig()


def test_training_record_renders_like_the_eval_request(tmp_path):
    rows = data.load_split("train")[:200]
    exs = build_data.build_examples(rows, QC)
    p = tmp_path / "t.jsonl"
    build_data.write_jsonl(p, [build_data.to_kev_record(e) for e in exs])
    recs = load_records(p)
    for ex, rec in zip(exs, recs):
        train_rec, _ = to_record(__import__("kev.api", fromlist=["SystemOneRequest"]).SystemOneRequest.model_validate(api_request(rec)))
        eval_rec, _ = to_record(build_request(ex.state, ex.questions))
        assert json.dumps(train_rec, sort_keys=True, default=str) == json.dumps(eval_rec, sort_keys=True, default=str), ex.query_id
