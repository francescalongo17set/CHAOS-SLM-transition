from dataclasses import dataclass

from contracts.common import Answer, ContextWindow


@dataclass(frozen=True)
class AgenticIn:
    question: str
    context: ContextWindow


@dataclass(frozen=True)
class AgenticOut:
    answer: Answer
