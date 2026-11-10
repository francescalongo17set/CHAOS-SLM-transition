import pytest

from safety_check.Contract import (
    ROUTE_ASK_CLARIFICATION,
    ROUTE_REFUSE,
    STATUS_ROUTES,
    SanitizedInput,
    validate_safety_result,
)
from safety_check.safetyCheck import VALID_MODES, SafetyCheckStub

CONTEXT = {
    "history": [
        {"role": "user", "content": "What is the third-party liability limit?"},
        {"role": "assistant", "content": "The limit is 1,000,000 EUR."},
    ],
    "selected_policy": "POLICY_1",
    "library": "LIBRARY_1",
}


@pytest.mark.parametrize("mode", VALID_MODES)
def test_every_mode_follows_the_contract(mode):
    result = SafetyCheckStub(mode).run("What is the deductible?", CONTEXT)
    assert validate_safety_result(result) == []


def test_pass_mode_returns_sanitized_input():
    result = SafetyCheckStub("pass").run("What is the deductible?", CONTEXT)
    assert result["safety_pass"] is True
    assert result["target_route"] is None
    sanitized = result["sanitized_input"]
    assert isinstance(sanitized, SanitizedInput)
    assert sanitized.question == "What is the deductible?"
    assert sanitized.history[0] == ("user", "What is the third-party liability limit?")
    assert sanitized.selected_policy == "POLICY_1"


@pytest.mark.parametrize(
    "mode,route",
    [
        ("too_long", ROUTE_ASK_CLARIFICATION),
        ("block", ROUTE_REFUSE),
        ("error", ROUTE_REFUSE),
    ],
)
def test_blocked_modes_have_no_payload_and_the_right_route(mode, route):
    result = SafetyCheckStub(mode).run("What is the deductible?", CONTEXT)
    assert result["safety_pass"] is False
    assert result["sanitized_input"] is None
    assert result["target_route"] == route
    assert route in STATUS_ROUTES[result["status_code"]]


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError):
        SafetyCheckStub("nonsense")


def test_validator_detects_contract_violations():
    good = SafetyCheckStub("block").run("q", CONTEXT)

    wrong_route = dict(good, target_route=ROUTE_ASK_CLARIFICATION)
    assert validate_safety_result(wrong_route) != []

    leaking_payload = dict(good, sanitized_input=SanitizedInput("q", (), "P", "L"))
    assert validate_safety_result(leaking_payload) != []

    missing_key = {k: v for k, v in good.items() if k != "status_code"}
    assert validate_safety_result(missing_key) != []

    assert validate_safety_result(None) != []