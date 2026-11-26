from dataclasses import dataclass

from contracts.common import Answer


@dataclass(frozen=True)
class VerificationIn:
    question: str
    route: str
    answer: Answer


@dataclass(frozen=True)
class VerificationOut:
    passed: bool
    answer: Answer  # what the user sees; when passed is False it must be a safe replacement
