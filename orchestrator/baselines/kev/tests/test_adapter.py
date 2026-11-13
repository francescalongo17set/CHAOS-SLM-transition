"""Adapter tests without torch: upstream kev.api is real (needs pydantic and the kev package on the path),
kev.model.admit and the model are stubs. Skipped if upstream kev is not importable."""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pytest.importorskip("kev.api")

from orchestrator.baselines.kev.adapter import KevScorer, build_request, probs_to_answer  # noqa: E402
from orchestrator.baselines.common import data  # noqa: E402
from orchestrator.baselines.common.logs import LogWriter, build_record, validate_log  # noqa: E402
from orchestrator.baselines.common.questions import QuestionConfig  # noqa: E402


class T:  # tensor stand-in
    def __init__(self, v): self.v = v
    def tolist(self): return list(self.v)


class FakeModel:
    """Peaks on option 0 everywhere, except the 6-option question (feature), which peaks on `feature_idx`."""
    def __init__(self, feature_idx): self.fi, self.calls = feature_idx, []
    def probs(self, enc):
        self.calls.append(enc["n_q"])
        out = []
        for k in enc["ks"]:
            idx = self.fi if k == 6 else 0
            out.append(T([0.8 if i == idx else 0.2 / (k - 1) for i in range(k)]))
        return out


@pytest.fixture(autouse=True)
def stub_admit(monkeypatch):
    m = types.ModuleType("kev.model")
    def admit(model, tok, rec):
        return {"ids": list(range(100 + 10 * len(rec["questions"]))), "state_tokens": 100,
                "n_q": len(rec["questions"]), "ks": [len(q["options"]) for q in rec["questions"]]}
    m.admit = admit
    monkeypatch.setitem(sys.modules, "kev.model", m)


FEATURES = ["regulatory_consultation", "product_policy_analysis", "comparison", "ibip_screening", "client_drafting", "none"]


def test_probs_to_answer():
    a = probs_to_answer(["a", "b"], [0.3, 0.7])
    assert a == {"label": "b", "probs": {"a": 0.3, "b": 0.7}, "option_order": ["a", "b"]}
    with pytest.raises(ValueError):
        probs_to_answer(["a"], [0.5, 0.5])


@pytest.mark.parametrize("fi", range(6))
def test_predict_is_one_call_with_three_questions(fi):
    q = QuestionConfig()
    row = data.load_split("validation")[0]
    model = FakeModel(fi)
    ans, st = KevScorer(None, model, "cpu").predict(row, q)
    assert ans["feature_classification"]["label"] == FEATURES[fi]
    assert set(ans) == {"scope_check", "feature_classification", "complexity_estimation"}   # v2: no slots
    assert model.calls == [3]
    assert st["input_native"] == 100 + 10 * 3
    for a in ans.values():
        assert abs(sum(a["probs"].values()) - 1) < 1e-3
        assert list(a["probs"]) == a["option_order"]


def test_record_text_shows_ids_and_text():
    from kev.api import to_record
    q = QuestionConfig()
    rec, meta = to_record(build_request('{"x": 1}', [q.scope_check()]))
    assert rec["state"] == '{"x": 1}'
    assert [m["keys"] for m in meta] == [["in_scope", "out_of_scope", "quick_reply"]]
    assert rec["questions"][0]["options"][0].startswith("in_scope: ")


def test_one_row_per_route_log_validates(tmp_path):
    """Five rows (one per gold route) through the fake model produce schema-valid lines."""
    q = QuestionConfig()
    seen, picked = set(), []
    for r in data.load_split("validation"):
        if r.support["expected_route"] not in seen:
            seen.add(r.support["expected_route"]); picked.append(r)
    assert len(picked) == 5
    meta = {"run_id": "t", "pipeline": "kev", "model_id": "m", "model_revision": "r", "split": "validation"}
    p = tmp_path / "validation.jsonl"
    with LogWriter(p) as w:
        for r in picked:
            ans, st = KevScorer(None, FakeModel(1), "cpu").predict(r, q)
            w.write(build_record(r, meta, ans, latency_ms=st["latency_ms"]))
    assert [e for e in validate_log(p, "validation") if "missing from log" not in e] == []
