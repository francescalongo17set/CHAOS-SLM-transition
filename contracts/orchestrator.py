"""Decision model + dispatcher."""
from dataclasses import dataclass
from typing import Optional

from contracts.common import ContextWindow

ROUTES = ("quick_reply", "refuse", "lightweight", "agentic")


@dataclass(frozen=True)
class OrchestratorIn:
    question: str
    context: ContextWindow
    tau: Optional[float] = None  # confidence threshold; unused until owner decision X-04


@dataclass(frozen=True)
class OrchestratorOut:
    route: str  # one of ROUTES
    reason: str
    confidence: float  # in [0, 1]
