"""Verification. STUB: passes every answer through unchecked."""
from contracts.verification import VerificationIn, VerificationOut


def run(x: VerificationIn) -> VerificationOut:
    return VerificationOut(passed=True, answer=x.answer)
