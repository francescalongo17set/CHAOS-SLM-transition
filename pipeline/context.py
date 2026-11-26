"""Builds the context window handed to the systems."""
from contracts.common import ContextWindow, Turn


def build_context(history=(), selected_policy: str = "", library: str = "") -> ContextWindow:
    """history: iterable of {"role": ..., "content": ...}."""
    return ContextWindow([Turn(t["role"], t["content"]) for t in history], selected_policy, library)
