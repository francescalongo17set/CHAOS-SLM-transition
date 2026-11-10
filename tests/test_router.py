import json

import pytest

from orch.decision import QUESTIONS, Decision
from orch.router import Orchestrator, Thresholds, route

TH = Thresholds(unsafe=0.3, out_of_scope=0.5, lightweight=0.8)


def D(**p):
    return Decision.from_probs(p)


def decs(unsafe=0.0, out=0.0, light=1.0):
    return {"safety": D(safe=1 - unsafe, unsafe=unsafe), "scope": D(in_scope=1 - out, out_of_scope=out),
            "complexity": D(lightweight=light, agentic=1 - light)}


def test_envelope():
    d = D(a=0.2, b=0.8)
    assert (d.decision, d.probability, d.alternatives) == ("b", 0.8, {"a": pytest.approx(0.2)})
    assert d.prob("a") == pytest.approx(0.2) and Decision.from_dict(d.to_dict()).decision == "b"


def test_unsafe_threshold_is_low_and_wins_over_everything():
    assert route(decs(unsafe=0.35, out=0.9), TH) == ("stop", "unsafe")
    assert route(decs(unsafe=0.29), TH).route == "lightweight"


def test_out_of_scope_stops():
    assert route(decs(out=0.5), TH) == ("stop", "out_of_scope")
    assert route(decs(out=0.49), TH).route == "lightweight"


@pytest.mark.parametrize("light,expected", [(0.95, "lightweight"), (0.80, "lightweight"), (0.79, "agentic"), (0.2, "agentic")])
def test_complexity_threshold_escalates_when_unsure(light, expected):
    assert route(decs(light=light), TH).route == expected


def test_raising_threshold_never_reduces_escalation():
    for light in (0.5, 0.7, 0.85, 0.99):
        routes = [route(decs(light=light), Thresholds(lightweight=t)).route for t in (0.5, 0.7, 0.9, 0.999)]
        assert routes == sorted(routes, key=lambda r: r == "agentic")  # once agentic, stays agentic


class Stub:
    """Stands in for any DecisionBackend: fixed answers per question."""
    name, version = "stub", "0"

    def __init__(self, **p):
        self.p = p  # {"safety": {"safe": .9, "unsafe": .1}, ...}

    def decide(self, state, question, choices):
        return Decision.from_probs(self.p[next(k for k, (q, _) in QUESTIONS.items() if q == question)])


GOOD = dict(safety={"safe": .95, "unsafe": .05}, scope={"in_scope": .9, "out_of_scope": .1}, complexity={"lightweight": .9, "agentic": .1})


def test_orchestrator_routes_with_any_backend():
    assert Orchestrator(Stub(**GOOD)).run("q").route == "lightweight"
    assert Orchestrator(Stub(**{**GOOD, "safety": {"safe": .4, "unsafe": .6}})).run("q").reason == "unsafe"


def test_decision_log_has_everything_needed(tmp_path):
    log = tmp_path / "log.jsonl"
    Orchestrator(Stub(**GOOD), TH, log).run("Quanto dura il termine per denunciare un sinistro?")
    rec = json.loads(log.read_text().splitlines()[0])
    assert {"ts", "query", "decisions", "thresholds", "route", "reason", "model", "model_version"} <= rec.keys()
    assert set(rec["decisions"]) == {"safety", "scope", "complexity"}
    assert set(rec["decisions"]["scope"]) == {"decision", "probability", "alternatives"}
    assert rec["thresholds"]["lightweight"] == 0.8
