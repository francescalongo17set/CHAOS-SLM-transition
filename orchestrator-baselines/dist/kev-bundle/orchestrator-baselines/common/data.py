"""Data loader (P0 step 2). Read-only: never rewrites, filters or fixes rows (rule 2).

Model-visible input (C-07) is kept strictly apart from gold (`labels`, `support`).
"""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data-generation" / "data" / "final"
SPLITS = ("train", "validation", "test")
EXPECTED_COUNTS = {"train": 2092, "validation": 298, "test": 593}


@dataclass(frozen=True)
class ModelInput:
    """Everything a model may see: history + query + available_docs (C-07)."""
    history: tuple
    query: str
    available_docs: tuple

    def to_dict(self):
        return {"available_docs": list(self.available_docs),
                "history": [dict(h) for h in self.history],
                "request": self.query}


@dataclass(frozen=True)
class Row:
    query_id: str
    pair_id: object
    model_input: ModelInput
    labels: dict      # gold, never shown to models
    support: dict     # gold/diagnostics, never shown to models


def _data_dir(data_dir):
    return Path(data_dir) if data_dir else DEFAULT_DATA_DIR


def manifest_sha256(split, data_dir=None):
    return hashlib.sha256((_data_dir(data_dir) / split / "manifest.json").read_bytes()).hexdigest()


def load_split(split, data_dir=None, check_count=True):
    if split not in SPLITS:
        raise ValueError(f"unknown split {split!r}")
    d = _data_dir(data_dir)
    manifest = json.loads((d / split / "manifest.json").read_text(encoding="utf-8"))
    rows, seen = [], set()
    with open(d / split / "router.jsonl", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r["query_id"] in seen:
                raise ValueError(f"duplicate query_id {r['query_id']} in {split}")
            seen.add(r["query_id"])
            ctx = r["context"]
            rows.append(Row(
                query_id=r["query_id"],
                pair_id=r["support"].get("pair_id"),
                model_input=ModelInput(
                    history=tuple({"role": h["role"], "text": h["text"]} for h in ctx["history"]),
                    query=r["query"],
                    available_docs=tuple(ctx["available_docs"])),
                labels=r["labels"],
                support=r["support"]))
    n = manifest["counts"]["router"]
    if len(rows) != n:
        raise ValueError(f"{split}: {len(rows)} rows but manifest says {n}")
    if check_count and split in EXPECTED_COUNTS and len(rows) != EXPECTED_COUNTS[split]:
        raise ValueError(f"{split}: {len(rows)} rows, expected {EXPECTED_COUNTS[split]}")
    return rows
