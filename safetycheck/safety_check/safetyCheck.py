"""Safety check stub.

Same interface as the real Safety check, so the rest of the pipeline can be
developed and tested before the real module exists. See Contract.py for the
full agreement on inputs, outputs and rules.

Modes (what the stub simulates):
    "pass"      input is safe, returns a SanitizedInput        (default)
    "too_long"  input too long -> "Ask for clarification"
    "block"     security block -> "Refuse and re-route"
    "error"     internal error (fail-closed) -> "Refuse and re-route"

To replace the stub with the real module, keep the same class interface:
    result = safety_check.run(broker_question, artificial_context_window)
"""

import time
import unicodedata
from typing import Any, Dict

try:  # used as part of the safety_check package
    from .Contract import (
        ROUTE_ASK_CLARIFICATION,
        ROUTE_REFUSE,
        STATUS_INTERNAL_ERROR,
        STATUS_OK,
        STATUS_PAYLOAD_TOO_LONG,
        STATUS_SECURITY_BLOCK,
        THREAT_INJECTION,
        THREAT_INTERNAL,
        THREAT_NONE,
        SanitizedInput,
    )
except ImportError:  # used as a flat folder of scripts (no package)
    from Contract import (
        ROUTE_ASK_CLARIFICATION,
        ROUTE_REFUSE,
        STATUS_INTERNAL_ERROR,
        STATUS_OK,
        STATUS_PAYLOAD_TOO_LONG,
        STATUS_SECURITY_BLOCK,
        THREAT_INJECTION,
        THREAT_INTERNAL,
        THREAT_NONE,
        SanitizedInput,
    )

# mode -> (status_code, threat_type, target_route, user_message)
_BLOCKED_OUTCOMES = {
    "too_long": (
        STATUS_PAYLOAD_TOO_LONG,
        THREAT_NONE,
        ROUTE_ASK_CLARIFICATION,
        "The text is too long. Please narrow it down to the relevant clause.",
    ),
    "block": (
        STATUS_SECURITY_BLOCK,
        THREAT_INJECTION,
        ROUTE_REFUSE,
        "The request cannot be processed because of security checks.",
    ),
    "error": (
        STATUS_INTERNAL_ERROR,
        THREAT_INTERNAL,
        ROUTE_REFUSE,
        "Service temporarily unavailable, please try again.",
    ),
}

VALID_MODES = ("pass",) + tuple(_BLOCKED_OUTCOMES)


class SafetyCheckStub:
    """Fake Safety check: no model, no real checks, contract-compliant output."""

    def __init__(self, mode: str = "pass"):
        if mode not in VALID_MODES:
            raise ValueError(f"unknown mode {mode!r}, expected one of {VALID_MODES}")
        self.mode = mode

    def run(
        self, broker_question: str, artificial_context_window: Dict[str, Any]
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()

        if self.mode in _BLOCKED_OUTCOMES:
            status, threat, route, message = _BLOCKED_OUTCOMES[self.mode]
            return {
                "safety_pass": False,
                "status_code": status,
                "threat_type": threat,
                "sub_code": f"STUB_{self.mode.upper()}",
                "risk_score": 0.0,
                "target_route": route,
                "user_message": message,
                "sanitized_input": None,
                "latency_ms": self._elapsed_ms(t0),
            }

        # In "pass" mode the stub inspects nothing and rejects nothing: every
        # input is accepted, even malformed ones, so it never crashes the
        # pipeline. Missing or odd fields are replaced with safe defaults.
        context = artificial_context_window or {}
        history = tuple(
            (str(turn.get("role", "user")), str(turn.get("content", "")))
            for turn in (context.get("history") or [])
            if isinstance(turn, dict)
        )
        sanitized = SanitizedInput(
            # The stub only applies NFC normalization; the real module also
            # removes invisible characters and runs the security checks.
            question=unicodedata.normalize("NFC", str(broker_question or "")),
            history=history,
            selected_policy=str(context.get("selected_policy") or ""),
            library=str(context.get("library") or ""),
        )
        return {
            "safety_pass": True,
            "status_code": STATUS_OK,
            "threat_type": THREAT_NONE,
            "sub_code": "STUB_PASS",
            "risk_score": 0.0,
            "target_route": None,
            "user_message": None,
            "sanitized_input": sanitized,
            "latency_ms": self._elapsed_ms(t0),
        }

    @staticmethod
    def _elapsed_ms(t0: float) -> float:
        return round((time.perf_counter() - t0) * 1000, 3)