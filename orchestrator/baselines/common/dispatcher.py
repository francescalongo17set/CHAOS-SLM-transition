"""Deterministic dispatcher (chapter 04, C-14). Rule table, first match wins."""

SENSITIVE_FEATURES = {"ibip_screening", "client_drafting"}
ROUTES = ("lightweight", "agentic", "clarification", "refuse", "quick_reply")


def dispatch(scope_check, feature, complexity, needs_clarification, tau=None, confidence=None):
    """Return the route for one orchestrator record.

    tau / confidence: the low-confidence -> agentic override is NOT implemented in
    round 1 (X-04 pending). Any non-None tau raises.
    """
    if tau is not None or confidence is not None:
        raise NotImplementedError("confidence override is pending owner decision X-04")
    if scope_check == "out_of_scope":
        return "refuse"
    if scope_check == "quick_reply":
        return "quick_reply"
    if needs_clarification:
        return "clarification"
    if feature in SENSITIVE_FEATURES or complexity == "complex":
        return "agentic"
    return "lightweight"


def gold_record(row):
    """Orchestrator record built from gold labels + support.slot_status (oracle test)."""
    lab, sup = row.labels, row.support
    needs = any(v != "present" for v in (sup.get("slot_status") or {}).values())
    return {"scope_check": lab["scope_check"], "feature": lab["feature"],
            "complexity": lab.get("complexity"), "needs_clarification": needs}


def dispatch_gold(row):
    return dispatch(**gold_record(row))
