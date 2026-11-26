"""Safety check. STUB: passes everything, filters nothing."""
from contracts.safety import SafetyIn, SafetyOut


def run(x: SafetyIn) -> SafetyOut:
    return SafetyOut(safety_pass=True, status_code="OK", question=x.question, context=x.context)
