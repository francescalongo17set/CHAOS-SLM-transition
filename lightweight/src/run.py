"""Lightweight. STUB: returns a placeholder answer with no sources."""
from contracts.common import Answer
from contracts.lightweight import LightweightIn, LightweightOut


def run(x: LightweightIn) -> LightweightOut:
    return LightweightOut(Answer("[lightweight stub] not implemented yet"))
