"""Safety check contract.

This module is the AGREEMENT between the Safety check block and the other
blocks of the pipeline (Orchestrator labels, Dispatcher, Answer writer). It
defines what goes in, what comes out, and the rules both sides must respect.
The stub (safetyCheck.py) and the real implementation must both follow it.

Position in the pipeline
------------------------
    Broker question -> Safety check -> Orchestrator labels -> Dispatcher -> ...

Scope
-----
The Safety check only handles adversarial security: prompt injection,
jailbreak, output hijacking and context manipulation.
It does NOT decide scope, complexity or missing info: those labels are
computed by the trained model in Orchestrator labels.

INPUT (what the Safety check receives)
--------------------------------------
broker_question : str
    Current question typed or pasted by the broker.
artificial_context_window : dict
    "history"         : list of {"role": "user" | "assistant", "content": str}
                        Assistant turns must contain the plain answer text
                        (the "risposta" field), not the raw JSON of the
                        Answer writer. Ideally the history is read
                        server-side, not sent by the client.
    "selected_policy" : str, ID of the selected policy (must exist in the KB)
    "library"         : str, ID of the library (must exist in the KB)

OUTPUT (what the Safety check returns): a dict with these keys
--------------------------------------------------------------
safety_pass     : bool          True only if the input can proceed.
status_code     : str           One of STATUS_ROUTES keys (see table below).
threat_type     : str           Macro-category of the threat (THREAT_* below).
sub_code        : str           Fine-grained code for internal logs only.
risk_score      : float         In [0.0, 1.0]. Compared with tau_safety.
target_route    : str | None    Route for the Dispatcher (see table below).
user_message    : str | None    Message to show to the broker, if any.
sanitized_input : SanitizedInput | None
                                The ONLY text downstream blocks may use.
latency_ms      : float         Execution time of the check.

STATUS CODE -> ROUTE TABLE
--------------------------
status_code        safety_pass  target_route              meaning
OK                 True         None                      input is safe, normal routing
PAYLOAD_TOO_LONG   False        Ask for clarification     operational limit, NOT an attack
SECURITY_BLOCK     False        Refuse and re-route       attack or invalid context
INTERNAL_ERROR     False        Refuse and re-route       timeout or model error (fail-closed)

RULES
-----
1. Downstream blocks use ONLY `sanitized_input`; the raw text is discarded
   (prevents time-of-check to time-of-use problems).
2. If `safety_pass` is False, `sanitized_input` is always None.
3. `safety_pass` is True if and only if `status_code` == "OK" and
   `target_route` is None.
4. `target_route` must be one of the routes allowed for the `status_code`
   (STATUS_ROUTES below).
5. Fail-closed: if the Safety check result is missing or malformed, the
   Dispatcher is expected to route to "Refuse and re-route".
   (This rule is implemented by the Dispatcher, not by this module.)
6. `user_message` for INTERNAL_ERROR must be neutral ("service temporarily
   unavailable"): a technical error is not the broker's fault.
7. `sub_code` and the real reason of a block go to the internal logs only,
   never to the broker.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# --- Status codes -----------------------------------------------------------
STATUS_OK = "OK"
STATUS_PAYLOAD_TOO_LONG = "PAYLOAD_TOO_LONG"
STATUS_SECURITY_BLOCK = "SECURITY_BLOCK"
STATUS_INTERNAL_ERROR = "INTERNAL_ERROR"

# --- Routes (names must match the Dispatcher stubs) -------------------------
ROUTE_ASK_CLARIFICATION = "Ask for clarification"
ROUTE_REFUSE = "Refuse and re-route"

# --- Threat types -----------------------------------------------------------
THREAT_NONE = "NONE"
THREAT_STRUCTURAL = "STRUCTURAL_OR_CONTEXT_VIOLATION"
THREAT_INJECTION = "ADVERSARIAL_PROMPT_INJECTION"
THREAT_INTERNAL = "INTERNAL_ERROR_FAIL_CLOSED"

# status_code -> routes allowed for that status (None = continue the pipeline)
STATUS_ROUTES: Dict[str, set] = {
    STATUS_OK: {None},
    STATUS_PAYLOAD_TOO_LONG: {ROUTE_ASK_CLARIFICATION},
    STATUS_SECURITY_BLOCK: {ROUTE_REFUSE},
    STATUS_INTERNAL_ERROR: {ROUTE_REFUSE},
}

RESULT_KEYS = (
    "safety_pass",
    "status_code",
    "threat_type",
    "sub_code",
    "risk_score",
    "target_route",
    "user_message",
    "sanitized_input",
    "latency_ms",
)


@dataclass(frozen=True)
class SanitizedInput:
    """The only object downstream blocks may read after a successful check.

    history is a tuple of (role, content) pairs so that it cannot be modified
    after the check.
    """

    question: str
    history: Tuple[Tuple[str, str], ...]
    selected_policy: str
    library: str


def validate_safety_result(result: Any) -> List[str]:
    """Check that a Safety check result follows the contract.

    Returns a list of error messages (empty list = result is valid).
    Used in tests to verify the stub and the real implementation; it is NOT
    the Dispatcher gate.
    """
    errors: List[str] = []
    if not isinstance(result, dict):
        return ["result is not a dict"]

    for key in RESULT_KEYS:
        if key not in result:
            errors.append(f"missing key: {key}")
    if errors:
        return errors

    safety_pass = result["safety_pass"]
    status = result["status_code"]
    route = result["target_route"]
    sanitized = result["sanitized_input"]
    score = result["risk_score"]

    if not isinstance(safety_pass, bool):
        errors.append("safety_pass must be a bool")
    if status not in STATUS_ROUTES:
        errors.append(f"unknown status_code: {status!r}")
    elif route not in STATUS_ROUTES[status]:
        errors.append(f"route {route!r} not allowed for status {status!r}")
    if isinstance(safety_pass, bool):
        if safety_pass != (status == STATUS_OK):
            errors.append("safety_pass must be True if and only if status_code is OK")
        if safety_pass and not isinstance(sanitized, SanitizedInput):
            errors.append("sanitized_input must be a SanitizedInput when safety_pass is True")
        if not safety_pass and sanitized is not None:
            errors.append("sanitized_input must be None when safety_pass is False")
    if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0.0 <= score <= 1.0:
        errors.append("risk_score must be a number in [0.0, 1.0]")
    if not isinstance(result["latency_ms"], (int, float)):
        errors.append("latency_ms must be a number")
    return errors