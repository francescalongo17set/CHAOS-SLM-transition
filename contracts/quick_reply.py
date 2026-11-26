from dataclasses import dataclass

from contracts.common import Answer, ContextWindow


@dataclass(frozen=True)
class QuickReplyIn:
    question: str
    context: ContextWindow


@dataclass(frozen=True)
class QuickReplyOut:
    answer: Answer
