import json
import copy
import pytest
import yaml

from common import data, state, dispatcher, questions

FORBIDDEN = {"labels", "support", "resolved_slots", "selected_doc_id"}


@pytest.mark.parametrize("split", ["validation", "test"])
def test_counts_and_manifest(split):
    rows = data.load_split(split)
    assert len(rows) == data.EXPECTED_COUNTS[split]
    assert len(data.manifest_sha256(split)) == 64


def test_model_input_has_no_gold():
    rows = data.load_split("test")
    for r in rows:
        d = r.model_input.to_dict()
        assert set(d) == {"available_docs", "history", "request"}
        blob = state.serialize_state(r.model_input)
        assert not (FORBIDDEN & set(json.loads(blob)))
        assert r.support["expected_route"] not in ("",)  # gold kept apart
        assert r.query_id.startswith("orc-")


def test_state_deterministic_and_shape():
    rows = data.load_split("test")
    r = next(x for x in rows if not x.model_input.history)
    a, b = state.serialize_state(r.model_input), state.serialize_state(r.model_input)
    assert a == b
    d = json.loads(a)
    assert list(d) == ["available_docs", "history", "request"]
    assert d["history"] == []
    assert d["available_docs"] == list(r.model_input.available_docs)  # verbatim, decoys kept
    assert d["request"] == r.model_input.query


def test_state_with_history_keeps_order():
    rows = data.load_split("test")
    r = next(x for x in rows if len(x.model_input.history) >= 2)
    d = json.loads(state.serialize_state(r.model_input))
    assert d["history"] == [dict(h) for h in r.model_input.history]


def test_state_keeps_non_ascii():
    mi = data.ModelInput(history=(), query="è già così", available_docs=("a",))
    assert "è già così" in state.serialize_state(mi)


def test_questions_default_loads():
    q = questions.QuestionConfig()
    assert q.scope_check().option_ids == questions.CANONICAL_OPTIONS["scope_check"]
    assert len(q.sha256) == 64
    qs = q.questions_for("ibip_screening")
    assert [x.qid for x in qs] == ["scope_check", "feature_classification",
                                   "complexity_estimation", "slot:product", "slot:client_profile"]
    assert q.questions_for("none")[-1].qid == "complexity_estimation"


def _write(tmp_path, mutate):
    cfg = yaml.safe_load(open(questions.DEFAULT_CONFIG))
    mutate(cfg)
    p = tmp_path / "q.yaml"
    p.write_text(yaml.safe_dump(cfg, allow_unicode=True))
    return p


def test_questions_reject_missing_option(tmp_path):
    p = _write(tmp_path, lambda c: c["scope_check"]["options"].pop())
    with pytest.raises(ValueError):
        questions.QuestionConfig(p)


def test_questions_reject_reordered_option(tmp_path):
    def m(c):
        o = c["complexity_estimation"]["options"]
        o[0], o[1] = o[1], o[0]
    with pytest.raises(ValueError):
        questions.QuestionConfig(_write(tmp_path, m))


def test_questions_reject_unknown_slot(tmp_path):
    p = _write(tmp_path, lambda c: c["slots"]["by_feature"].__setitem__("comparison", ["bogus"]))
    with pytest.raises(ValueError):
        questions.QuestionConfig(p)


ROUTE_CASES = [
    (("out_of_scope", "none", None, False), "refuse"),
    (("out_of_scope", "none", None, True), "refuse"),
    (("quick_reply", "none", None, False), "quick_reply"),
    (("in_scope", "ibip_screening", "complex", True), "clarification"),
    (("in_scope", "ibip_screening", "simple", False), "agentic"),
    (("in_scope", "client_drafting", "simple", False), "agentic"),
    (("in_scope", "comparison", "complex", False), "agentic"),
    (("in_scope", "comparison", "simple", False), "lightweight"),
]


@pytest.mark.parametrize("args,expected", ROUTE_CASES)
def test_dispatch_rules(args, expected):
    assert dispatcher.dispatch(*args) == expected


def test_dispatch_rejects_tau():
    with pytest.raises(NotImplementedError):
        dispatcher.dispatch("in_scope", "comparison", "simple", False, tau=0.5)


def test_regulatory_asks_only_topic():
    assert questions.QuestionConfig().slots_for_feature("regulatory_consultation") == ["topic"]
