"""Plain-code routing: thresholds turn the three decisions into stop / lightweight / agentic."""
import json
import time
from dataclasses import asdict, dataclass
from typing import NamedTuple

from orch.decision import QUESTIONS, Decision, DecisionBackend

COST = {"stop": 0.0, "lightweight": 1.0, "agentic": 5.0}  # relative cost units; agentic is a parameter in eval


@dataclass(frozen=True)
class Thresholds:
    unsafe: float = 0.30        # stop if P(unsafe) >= this. Low on purpose: missing an attack is worse than a false block.
    out_of_scope: float = 0.50  # stop if P(out_of_scope) >= this
    lightweight: float = 0.80   # go lightweight only if P(lightweight) >= this, otherwise escalate. The knob we sweep.


class Route(NamedTuple):
    route: str   # stop | lightweight | agentic
    reason: str


def route(d: dict, th: Thresholds) -> Route:
    """d maps 'safety' | 'scope' | 'complexity' to Decision. Order matters: safety, then scope, then complexity."""
    if d["safety"].prob("unsafe") >= th.unsafe:
        return Route("stop", "unsafe")
    if d["scope"].prob("out_of_scope") >= th.out_of_scope:
        return Route("stop", "out_of_scope")
    if d["complexity"].prob("lightweight") >= th.lightweight:
        return Route("lightweight", "confident_lightweight")
    return Route("agentic", "complex_or_unsure")


def log_record(query, d, th, r, backend) -> dict:
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "query": query,
            "decisions": {k: v.to_dict() for k, v in d.items()},
            "thresholds": asdict(th), "route": r.route, "reason": r.reason,
            "model": backend.name, "model_version": backend.version}


class Orchestrator:
    """Asks the backend the three questions, applies thresholds, appends one JSONL line per query.
    It never answers the query. shortcut: all three questions are always asked (no early stop on unsafe);
    add short-circuiting if orchestrator latency ever matters."""

    def __init__(self, backend: DecisionBackend, th: Thresholds = Thresholds(), log_path=None):
        self.backend, self.th, self.log_path = backend, th, log_path

    def run(self, query: str, context: str = "") -> Route:
        state = f"{context}\n{query}".strip()
        d = {k: self.backend.decide(state, q, ch) for k, (q, ch) in QUESTIONS.items()}
        r = route(d, self.th)
        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_record(query, d, self.th, r, self.backend), ensure_ascii=False) + "\n")
        return r
