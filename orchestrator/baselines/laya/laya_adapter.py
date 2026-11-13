"""Laya adapter (plan P2, handbook chapters 03, 06, 09).

Canonical questions -> Laya `choice` questions; Laya results -> canonical log line.
Does not import the `laya` library, so it is testable with a stand-in agent.
Result keys (`answers[qid]["choice"|"probabilities"]`, `usage`) read from the laya 0.4.31 source;
the smoke test confirms them on the real model.

This folder has no __init__.py on purpose: a package named `laya` here would hide the
installed `laya` library.
"""
from orchestrator.baselines.common.dispatcher import ROUTES
from orchestrator.baselines.common.logs import build_record


def route_rows(rows):
    """First row of each route, in route order (the 5 rows of the unit and smoke tests)."""
    first = {}
    for r in rows:
        first.setdefault(r.support["expected_route"], r)
    return [first[route] for route in ROUTES]


def to_laya(questions):
    """Canonical Question list -> Laya questions dict (criteria in canonical order, P-02)."""
    return {q.qid: {"type": "choice", "instructions": q.instructions, "criteria": dict(q.options)}
            for q in questions}


def to_answer(laya_answer, question):
    """One Laya choice answer -> canonical {label, probs, option_order}. Raises if the shape is off."""
    probs = laya_answer["probabilities"]
    if set(probs) != set(question.option_ids):
        raise ValueError(f"{question.qid}: Laya options {sorted(probs)} != {sorted(question.option_ids)}")
    return {"label": laya_answer["choice"],
            "probs": {o: float(probs[o]) for o in question.option_ids},
            "option_order": question.option_ids}


def predict_row(agent, qcfg, state_text):
    """Two calls (C-23): core questions, then the slot questions of the predicted feature.

    Returns (core questions, slot questions, result 1, result 2 or None).
    """
    core = qcfg.questions_for("none")  # the 3 fixed questions; `none` asks no slots
    res_a = agent.predict(state_text, to_laya(core))
    feature = res_a["answers"]["feature_classification"]["choice"]
    slot_qs = [qcfg.slot_question(s) for s in qcfg.slots_for_feature(feature)]
    res_b = agent.predict(state_text, to_laya(slot_qs)) if slot_qs else None
    return core, slot_qs, res_a, res_b


def make_record(row, meta, core, slot_qs, res_a, res_b, latency_ms, is_warmup, input_ref):
    answers = {q.qid: to_answer(res_a["answers"][q.qid], q) for q in core}
    answers["slots"] = {q.qid.split(":", 1)[1]: to_answer(res_b["answers"][q.qid], q) for q in slot_qs}
    usage = {"call_1": res_a["usage"]}
    if res_b is not None:
        usage["call_2"] = res_b["usage"]
    dropped = max(u["state_tokens_dropped"] for u in usage.values())
    return build_record(
        row, meta, answers,
        latency_ms=latency_ms, is_warmup=is_warmup,
        tokens={"input_native": sum(u["input_tokens"] for u in usage.values()),
                "input_ref": input_ref, "output_native": None, "usage_reported": usage},
        truncated=dropped > 0, tokens_dropped=dropped)


def error_record(row, meta, error, latency_ms, is_warmup):
    rec = build_record(row, meta, {}, error=error, latency_ms=latency_ms, is_warmup=is_warmup)
    rec["answers"] = None  # chapter 06: a failed call logs answers: null
    return rec
