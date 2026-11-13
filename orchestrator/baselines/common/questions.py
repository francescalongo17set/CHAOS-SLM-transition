"""Question config loader (P0 step 4). Wording lives in questions.<lang>.yaml (C-21).

Option ids and order are fixed here and checked against the file (chapter 03, P-02).
"""
import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parent / "questions.en.yaml"

CANONICAL_OPTIONS = {
    "scope_check": ["in_scope", "out_of_scope", "quick_reply"],
    "feature_classification": ["regulatory_consultation", "product_policy_analysis",
                               "comparison", "ibip_screening", "client_drafting", "none"],
    "complexity_estimation": ["simple", "complex"],
    "slots": ["present", "missing", "ambiguous"],
}
SLOT_IDS = ["insurer", "product", "field", "coverage", "topic", "date_reference",
            "client_profile", "message_goal"]


@dataclass(frozen=True)
class Question:
    qid: str
    instructions: str
    options: tuple          # ((id, text), ...) in canonical order

    @property
    def option_ids(self):
        return [o[0] for o in self.options]


class QuestionConfig:
    def __init__(self, path=DEFAULT_CONFIG):
        path = Path(path)
        raw = path.read_bytes()
        self.path = path
        self.sha256 = hashlib.sha256(raw).hexdigest()
        cfg = yaml.safe_load(raw)
        self._cfg = cfg
        for key, canon in CANONICAL_OPTIONS.items():
            if key not in cfg:
                raise ValueError(f"{path.name}: missing section {key!r}")
            ids = [o["id"] for o in cfg[key]["options"]]
            if ids != canon:
                raise ValueError(f"{path.name}: options of {key!r} are {ids}, expected {canon} in this order")
            for o in cfg[key]["options"]:
                if not str(o.get("text", "")).strip():
                    raise ValueError(f"{path.name}: empty text for {key}.{o['id']}")
        desc = cfg["slots"].get("descriptions", {})
        if set(desc) != set(SLOT_IDS):
            raise ValueError(f"{path.name}: slot descriptions must cover exactly {SLOT_IDS}")
        by = cfg["slots"]["by_feature"]
        for f, slots in by.items():
            for s in slots:
                if s not in SLOT_IDS:
                    raise ValueError(f"{path.name}: unknown slot {s!r} for feature {f!r}")
        if set(by) != set(CANONICAL_OPTIONS["feature_classification"]):
            raise ValueError(f"{path.name}: by_feature must cover every feature option")
        if "{slot_description}" not in cfg["slots"]["instructions"]:
            raise ValueError(f"{path.name}: slots.instructions needs {{slot_description}}")

    def _q(self, qid, key, instructions):
        sec = self._cfg[key]
        return Question(qid, instructions, tuple((o["id"], o["text"].strip()) for o in sec["options"]))

    def scope_check(self):
        return self._q("scope_check", "scope_check", self._cfg["scope_check"]["instructions"].strip())

    def feature_classification(self):
        return self._q("feature_classification", "feature_classification",
                       self._cfg["feature_classification"]["instructions"].strip())

    def complexity_estimation(self):
        return self._q("complexity_estimation", "complexity_estimation",
                       self._cfg["complexity_estimation"]["instructions"].strip())

    def slot_question(self, slot):
        s = self._cfg["slots"]
        ins = s["instructions"].strip().format(slot_description=s["descriptions"][slot])
        return self._q(f"slot:{slot}", "slots", ins)

    def slots_for_feature(self, feature):
        return list(self._cfg["slots"]["by_feature"][feature])

    def questions_for(self, predicted_feature):
        """Fixed questions plus slot questions of the predicted feature (C-23)."""
        qs = [self.scope_check(), self.feature_classification(), self.complexity_estimation()]
        qs += [self.slot_question(s) for s in self.slots_for_feature(predicted_feature)]
        return qs
