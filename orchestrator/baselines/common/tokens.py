"""Reference token counter (P-08, L-01): Qwen3.5 tokenizer, shared by all pipelines.

Verified in session (12 Nov 2026): tokenizer.json of Qwen3.5-0.8B-Base, 4B-Base and 9B-Base
is byte-identical (sha256 starts fe000e3ed39ed12b). Pinned to the 0.8B-Base revision below.
"""
from tokenizers import Tokenizer

REF_TOKENIZER_ID = "Qwen/Qwen3.5-0.8B-Base"
REF_TOKENIZER_REVISION = "dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68"


def render_questions(questions):
    """Canonical text of the question set (same rendering for every pipeline)."""
    parts = []
    for q in questions:
        lines = [f"[{q.qid}] {q.instructions}"]
        lines += [f"- {oid}: {text}" for oid, text in q.options]
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


class RefTokenizer:
    def __init__(self, tokenizer_id=REF_TOKENIZER_ID, revision=REF_TOKENIZER_REVISION):
        self.tokenizer_id, self.revision = tokenizer_id, revision
        self._tok = Tokenizer.from_pretrained(tokenizer_id, revision=revision)

    def count(self, text):
        return len(self._tok.encode(text, add_special_tokens=False).ids)

    def count_state(self, state_text):
        return self.count(state_text)

    def count_ref(self, state_text, questions):
        """input_tokens_ref: serialized state + question text, tokenized once."""
        return self.count(state_text + "\n\n" + render_questions(questions))
