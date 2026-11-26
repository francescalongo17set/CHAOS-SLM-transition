from dataclasses import dataclass, field


@dataclass(frozen=True)
class Turn:
    role: str  # "user" | "assistant"
    content: str  # assistant turns hold the plain answer text


@dataclass(frozen=True)
class ContextWindow:
    history: list[Turn] = field(default_factory=list)
    selected_policy: str = ""
    library: str = ""


@dataclass(frozen=True)
class Source:
    id: str
    text: str


@dataclass(frozen=True)
class Answer:
    text: str
    sources: list[Source] = field(default_factory=list)
