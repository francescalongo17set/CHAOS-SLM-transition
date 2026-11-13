"""Adapter unit test on 4 rows, one per route, with a stand-in agent (no laya, no model, no GPU).

Run from orchestrator/baselines/:  pytest laya/tests
"""
import hashlib
import sys
from pathlib import Path

from orchestrator.baselines.common import data
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # laya/ (flat modules, no package)

import orchestrator.baselines.laya.laya_adapter as A  # noqa: E402
from orchestrator.baselines.common import state  # noqa: E402
from orchestrator.baselines.common.dispatcher import ROUTES  # noqa: E402
from orchestrator.baselines.common.logs import LogWriter, validate_log  # noqa: E402
from orchestrator.baselines.common.questions import QuestionConfig  # noqa: E402

META = {"run_id": "laya-test", "pipeline": "laya", "model_id": "stand-in",
        "model_revision": "none", "split": "validation"}


class StandIn:
    """Answers like laya 0.4.31: choice, 4-decimal probabilities, usage with truncation keys."""

    def __init__(self, drop_probs=False, dropped=0):
        self.calls, self.drop_probs, self.dropped = [], drop_probs, dropped

    def predict(self, st, questions):
        self.calls.append(list(questions))
        answers = {}
        for qid, q in questions.items():
            opts = list(q["criteria"])
            w = [int(hashlib.sha256(f"{st}|{qid}|{o}".encode()).hexdigest()[:6], 16) + 1 for o in opts]
            p = [round(x / sum(w), 4) for x in w]
            ans = {"type": "choice", "choice": opts[p.index(max(p))], "confidence": 0.5}
            if not self.drop_probs:
                ans["probabilities"] = dict(zip(opts, p))
            answers[qid] = ans
        usage = {"input_tokens": 40 * len(questions), "output_tokens": 0, "state_tokens": 30,
                 "state_tokens_dropped": self.dropped, "truncated": self.dropped > 0,
                 "truncated_questions": []}
        return {"model": "laya-rl-agent", "answers": answers, "usage": usage}


def _record(agent, row, q):
    st = state.serialize_state(row.model_input)
    core, res = A.predict_row(agent, q, st)
    return A.make_record(row, META, core, res, 1.0, False, 99)


@pytest.fixture(scope="module")
def five():  # one row per route (4 in v2)
    return A.route_rows(data.load_split("validation"))


def test_route_rows_one_per_route(five):
    assert [r.support["expected_route"] for r in five] == list(ROUTES)


def test_routes_lines_pass_the_shared_validator(five, tmp_path):
    q = QuestionConfig()
    log = tmp_path / "validation.jsonl"
    with LogWriter(log) as w:
        for r in five:
            w.write(_record(StandIn(), r, q))
        w.write(A.error_record(data.load_split("validation")[-1], META, "boom", 2.0, False))
    errs = validate_log(log, "validation")
    # only complaint allowed: the rest of the split is not in this 6-line log
    assert len(errs) == 1 and "missing from log" in errs[0], errs


def test_one_call_three_questions(five):
    q = QuestionConfig()
    for r in five:
        agent = StandIn()
        rec = _record(agent, r, q)
        assert len(agent.calls) == 1
        assert agent.calls[0] == ["scope_check", "feature_classification", "complexity_estimation"]
        assert set(rec["answers"]) == {"scope_check", "feature_classification", "complexity_estimation"}
        assert rec["tokens"]["input_native"] == 40 * 3
        assert rec["temperature_applied"] is None


def test_missing_probabilities_raises(five):
    with pytest.raises(KeyError):
        _record(StandIn(drop_probs=True), five[0], QuestionConfig())


def test_truncation_is_logged(five):
    rec = _record(StandIn(dropped=7), five[0], QuestionConfig())
    assert rec["truncated"] is True and rec["tokens_dropped"] == 7
