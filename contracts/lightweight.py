"""RAG + answer writer."""
from dataclasses import dataclass

from contracts.common import Answer, ContextWindow


@dataclass(frozen=True)
class LightweightIn:
    question: str
    context: ContextWindow


@dataclass(frozen=True)
class LightweightOut:
    answer: Answer
