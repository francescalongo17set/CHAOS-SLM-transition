"""Agentic. STUB: returns a placeholder answer with no sources."""
from contracts.common import Answer
from contracts.agentic import AgenticIn, AgenticOut


def run(x: AgenticIn) -> AgenticOut:
    return AgenticOut(Answer("[agentic stub] not implemented yet"))
