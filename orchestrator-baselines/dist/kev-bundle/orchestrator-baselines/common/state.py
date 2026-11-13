"""State serializer (P-01). One JSON text per row, fixed key order, fixed spacing.

Detail fixed here (listed for owner review): single-line JSON with Python's default
separators and ensure_ascii=False, so Italian accents stay as characters.
"""
import json

from .data import ModelInput


def serialize_state(model_input: ModelInput) -> str:
    return json.dumps(model_input.to_dict(), ensure_ascii=False)
