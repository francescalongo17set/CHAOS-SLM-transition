"""FT-P0 steps 2-3 and 7: build training examples (chapter 02 rules) and write the Kev / Laya JSONL + manifest.

  python orchestrator/fine-tuning/common/build_data.py [--out orchestrator/fine-tuning/data]

Reuses the baselines package (state serialization, question wording, row loader). Never edits a row (rule 2).
Upstream `kev.model.fits` (zero drops) needs torch + kev, so it runs in the notebook, not here: see `kev_records_for_fits`.
"""
import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE))
sys.path.append(str(HERE.parents[2]))

from orchestrator.baselines.common import data                        # noqa: E402
from orchestrator.baselines.common.questions import QuestionConfig    # noqa: E402
from orchestrator.baselines.common.state import serialize_state       # noqa: E402

SEED = 20261113


@dataclass
class Example:
    query_id: str
    state: str                  # serialize_state(row.model_input), a string
    questions: list             # list[Question], order: scope, feature, complexity (if labelled); v2: no slot questions
    labels: dict                # qid -> option id (gold)


def build_example(row, qc):
    feature = row.labels["feature"]
    qs = [qc.scope_check(), qc.feature_classification()]
    labels = {"scope_check": row.labels["scope_check"], "feature_classification": feature}
    if "complexity" in row.labels:                       # in_scope rows only
        qs.append(qc.complexity_estimation())
        labels["complexity_estimation"] = row.labels["complexity"]
    ex = Example(row.query_id, serialize_state(row.model_input), qs, labels)
    for q in ex.questions:                               # label validity
        assert ex.labels[q.qid] in q.option_ids, (row.query_id, q.qid, ex.labels[q.qid])
    return ex


def build_examples(rows, qc=None):
    qc = qc or QuestionConfig()
    return [build_example(r, qc) for r in rows]


def _q_obj(q):
    return {"type": "choice", "instructions": q.instructions, "criteria": {oid: t for oid, t in q.options}}


def to_kev_record(ex):
    """Same construction as kev/adapter.py:build_request; the label sits inside each question (kev/data.py)."""
    return {"state": ex.state,
            "questions": {q.qid: {**_q_obj(q), "label": ex.labels[q.qid]} for q in ex.questions}}


def to_laya_record(ex):
    return {"state": ex.state,
            "questions": {q.qid: _q_obj(q) for q in ex.questions},
            "expected": {q.qid: ex.labels[q.qid] for q in ex.questions}}


def write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import checks
    import split
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE.parent / "data"))
    a = ap.parse_args()
    out = Path(a.out)
    qc = QuestionConfig()
    train_rows = data.load_split("train")
    val_rows = data.load_split("validation")
    train_ids, calib_ids = split.calibration_split(train_rows, seed=SEED)
    by_id = {r.query_id: r for r in train_rows}
    parts = {"train": [by_id[i] for i in train_ids],       # keeps original file order
             "calibration": [by_id[i] for i in calib_ids],
             "development": val_rows}
    checks.check_partitions(parts, test_ids={r.query_id for r in data.load_split("test")})
    manifest = {"seed": SEED, "question_config_sha256": qc.sha256,
                "source_manifests_sha256": {s: data.manifest_sha256(s) for s in data.SPLITS},
                "counts": {k: len(v) for k, v in parts.items()},
                "route_counts": {k: split.route_counts(v) for k, v in parts.items()}, "files": {}}
    for name, rows in parts.items():
        exs = build_examples(rows, qc)
        for fmt, fn in (("kev", to_kev_record), ("laya", to_laya_record)):
            p = out / fmt / f"{name}.jsonl"
            manifest["files"][f"{fmt}/{name}.jsonl"] = {"rows": len(exs), "sha256": write_jsonl(p, [fn(e) for e in exs])}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"]), "->", out)


if __name__ == "__main__":
    main()
