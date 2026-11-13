"""Kev adapter (P1 step 3): canonical state + question config -> Kev record; Kev probabilities -> canonical answers.

Imports `common/` (never the reverse). `kev.api.to_record` / `kev.model.admit` are the upstream (jaredpalmer/kev)
functions, imported lazily so the mapping can be unit-tested without torch. Upstream `kev` must be installed;
this folder is NOT importable as `kev` (no __init__.py) and must never shadow it.

Call sequence (verified against kev@2074cc4, serve.py / model.py / api.py):
  rec, meta = kev.api.to_record(SystemOneRequest(...))   # same text the HTTP API would build
  enc       = kev.model.admit(model, tok, rec)            # strict: a too-long state raises ContextOverflow (no truncation)
  probs     = model.probs(enc)                            # list[Tensor], one softmax per question, head temperature applied
"""
import time

from orchestrator.baselines.common.questions import CANONICAL_OPTIONS
from orchestrator.baselines.common.state import serialize_state

CORE_IDS = ("scope_check", "feature_classification", "complexity_estimation")


def build_request(state_text, questions):
    """Canonical Question objects (common.questions) -> kev SystemOneRequest. Option text is shown as `id: text`
    by Kev itself; option order is the canonical order (P-02)."""
    from kev.api import SystemOneRequest
    qs = {q.qid: {"type": "choice", "instructions": q.instructions,
                  "criteria": {oid: text for oid, text in q.options}} for q in questions}
    return SystemOneRequest(state=state_text, model="kev-latest", questions=qs)


def probs_to_answer(option_ids, probs):
    p = [float(x) for x in probs]
    if len(p) != len(option_ids):
        raise ValueError(f"{len(p)} probabilities for {len(option_ids)} options")
    d = dict(zip(option_ids, p))
    return {"label": max(d, key=d.get), "probs": d, "option_order": list(option_ids)}


class KevScorer:
    """One loaded Kev checkpoint. `predict(row, qconfig)` returns the canonical pieces of one log line."""

    def __init__(self, tok, model, device, sync=None):
        self.tok, self.model, self.device = tok, model, device
        self._sync = sync or (lambda: None)

    def _call(self, state_text, questions):
        from kev.api import to_record
        from kev.model import admit
        rec, _meta = to_record(build_request(state_text, questions))
        enc = admit(self.model, self.tok, rec)          # strict; raises ContextOverflow on a too-long state
        ps = self.model.probs(enc)
        return [q.tolist() for q in ps], {"tokens": len(enc["ids"]), "state_tokens": enc["state_tokens"]}

    def predict(self, row, qconfig):
        """-> (answers, stats). Two calls: core questions, then the slot questions of the PREDICTED feature (C-23).
        Questions are isolated in Kev (each its own row), so asking the slots in a second call gives the same
        probabilities as asking them in the first; the second call is made so the cascade and the token/latency
        accounting match what a real orchestrator would do. Time = the sum of the calls (chapter 05)."""
        state = serialize_state(row.model_input)
        self._sync(); t0 = time.perf_counter()
        core = [qconfig.scope_check(), qconfig.feature_classification(), qconfig.complexity_estimation()]
        ps, s1 = self._call(state, core)
        answers = {q.qid: probs_to_answer(q.option_ids, p) for q, p in zip(core, ps)}
        feature = answers["feature_classification"]["label"]
        slot_qs = [qconfig.slot_question(s) for s in qconfig.slots_for_feature(feature)]
        slots, usage = {}, [s1]
        if slot_qs:
            ps2, s2 = self._call(state, slot_qs)
            usage.append(s2)
            slots = {q.qid.split(":", 1)[1]: probs_to_answer(CANONICAL_OPTIONS["slots"], p) for q, p in zip(slot_qs, ps2)}
        self._sync()
        latency_ms = (time.perf_counter() - t0) * 1000.0
        answers["slots"] = slots
        return answers, {
            "latency_ms": latency_ms,
            "questions": core + slot_qs,
            "state_text": state,
            "input_native": sum(u["tokens"] for u in usage),     # state recomputed per call, question rows once each
            "usage_reported": {"input_tokens": [u["tokens"] for u in usage], "state_tokens": s1["state_tokens"]},
        }
