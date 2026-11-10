"""The one decision model: Laya, an encoder-based decision model (no LLM, no text generation).

Laya reads the text and the typed question once and returns a probability per option. API used here is the one
documented in its README / model card: laya.load(path) -> agent.predict(state, questions) ->
result["answers"][qid]["probabilities"].
"""
import hashlib
import os

from orch.decision import Decision

BASE_MODEL = "convaiinnovations/laya-multilingual"  # Apache-2.0, ~322M, mmBERT encoder; near-chance until fine-tuned


def model_version(path: str) -> str:
    """Pin the exact weights: sha256 prefix of the weights file for a local dir, the Hub id otherwise."""
    f = os.path.join(path, "model.safetensors")
    if not os.path.exists(f):
        return path
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


class LayaBackend:
    """DecisionBackend over a Laya agent. Pass `agent` to inject a stand-in (unit tests); otherwise it loads `path`."""

    def __init__(self, path=BASE_MODEL, agent=None):
        if agent is None:
            import laya  # only installed on Kaggle, see scripts/make_kaggle.py
            agent = laya.load(path)
        self.agent = agent
        self.name = "laya:" + os.path.basename(os.path.normpath(path))
        self.version = model_version(path)

    def decide(self, state, question, choices):
        q = {"q": {"type": "choice", "instructions": question, "criteria": dict(choices)}}
        probs = self.agent.predict(state, q)["answers"]["q"]["probabilities"]
        return Decision.from_probs({str(k): float(v) for k, v in probs.items()})
