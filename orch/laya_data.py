"""Turn our labelled rows into Laya's fine-tuning format: {"state", "questions", "expected"} per line."""
import json

from orch.decision import QUESTIONS


def questions_for(row) -> dict:
    """Same three typed questions the orchestrator asks at run time. Complexity only exists for in-scope safe rows."""
    keys = ["safety", "scope"] + (["complexity"] if row["complexity"] != "n/a" else [])
    return {k: {"type": "choice", "instructions": QUESTIONS[k][0], "criteria": dict(QUESTIONS[k][1])} for k in keys}


def to_laya_row(row) -> dict:
    qs = questions_for(row)
    return {"state": row["query"], "questions": qs, "expected": {k: row[k] for k in qs}}


def write_laya_jsonl(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(to_laya_row(r), ensure_ascii=False) + "\n")
