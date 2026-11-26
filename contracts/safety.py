from dataclasses import dataclass
from typing import Optional

from contracts.common import ContextWindow


@dataclass(frozen=True)
class SafetyIn:
    question: str
    context: ContextWindow


@dataclass(frozen=True)
class SafetyOut:
    """question and context are the sanitized copies, the only ones used downstream; None when blocked."""

    safety_pass: bool
    status_code: str  # "OK" when safety_pass, otherwise a block code
    question: Optional[str] = None
    context: Optional[ContextWindow] = None
    user_message: Optional[str] = None  # shown to the broker when blocked
