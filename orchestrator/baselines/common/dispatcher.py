"""Deterministic dispatcher, v2 (no clarification route). Rule table, first match wins.

v2 (owner decision 13 Nov, option B): missing information is handled by the agent / response path,
so the orchestrator no longer decides it and a missing slot never changes the route."""

SENSITIVE_FEATURES = {"ibip_screening", "client_drafting"}
ROUTES = ("lightweight", "agentic", "refuse", "quick_reply")


def dispatch(scope_check, feature, complexity, tau=None, confidence=None):
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
    if feature in SENSITIVE_FEATURES or complexity == "complex":
        return "agentic"
    return "lightweight"


def gold_record(row):
    """Orchestrator record built from gold labels (oracle test)."""
    lab = row.labels
    return {"scope_check": lab["scope_check"], "feature": lab["feature"], "complexity": lab.get("complexity")}


def dispatch_gold(row):
    return dispatch(**gold_record(row))
