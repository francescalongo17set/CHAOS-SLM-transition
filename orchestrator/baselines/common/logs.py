"""Prediction log writer and validator (chapter 06, P-07). v2: no slot answers, no needs_clarification."""
import json
import math
import os
from pathlib import Path

from . import data
from .questions import CANONICAL_OPTIONS, QuestionConfig  # noqa: F401

PIPELINES = {"kev", "laya", "nimble"}
CORE = ("scope_check", "feature_classification", "complexity_estimation")
REQUIRED_KEYS = ("run_id", "pipeline", "model_id", "model_revision", "split", "query_id",
                 "answers", "temperature_applied",
                 "latency_ms", "is_warmup", "tokens", "truncated", "tokens_dropped", "error")


class LogWriter:
    """Append one JSON line per request and flush (fsync). Resumable: see done_ids()."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._done = self.done_ids()
        self._f = open(self.path, "a", encoding="utf-8")

    def done_ids(self):
        ids = set()
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                for line in f:
                    try:
                        ids.add(json.loads(line)["query_id"])
                    except (json.JSONDecodeError, KeyError):
                        pass  # a torn last line from a killed run is ignored (and re-run)
        return ids

    def is_done(self, query_id):
        return query_id in self._done

    def write(self, record):
        qid = record["query_id"]
        if qid in self._done:
            raise ValueError(f"{qid} already logged")
        self._f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._f.flush()
        os.fsync(self._f.fileno())
        self._done.add(qid)

    def close(self):
        self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def read_log(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                out.append({"_bad_line": i})
    return out


def _check_answer(name, ans, options, errs, qid):
    if not isinstance(ans, dict) or "label" not in ans or "probs" not in ans:
        errs.append(f"{qid}: {name} malformed")
        return
    probs = ans["probs"]
    if set(probs) != set(options):
        errs.append(f"{qid}: {name} probs keys {sorted(probs)} != options {sorted(options)}")
        return
    if any((not isinstance(v, (int, float))) or math.isnan(v) or v < 0 for v in probs.values()):
        errs.append(f"{qid}: {name} invalid probability")
        return
    if abs(sum(probs.values()) - 1.0) > 1e-3:
        errs.append(f"{qid}: {name} probs sum {sum(probs.values()):.4f}")
    if ans["label"] not in options:
        errs.append(f"{qid}: {name} label {ans['label']!r} not an option")
    order = ans.get("option_order")
    if order is not None and list(order) != list(options):
        errs.append(f"{qid}: {name} option_order {order} != canonical {list(options)} (P-02)")


def validate_log(path, split, data_dir=None, qconfig=None):
    """Return a list of error strings; empty means the run is accepted."""
    qconfig = qconfig or QuestionConfig()
    rows = {r.query_id: r for r in data.load_split(split, data_dir)}
    recs = read_log(path)
    errs, seen = [], set()
    for rec in recs:
        if "_bad_line" in rec:
            errs.append(f"line {rec['_bad_line']}: unparseable JSON")
            continue
        qid = rec.get("query_id")
        miss = [k for k in REQUIRED_KEYS if k not in rec]
        if miss:
            errs.append(f"{qid}: missing keys {miss}")
            continue
        if qid in seen:
            errs.append(f"{qid}: duplicate")
        seen.add(qid)
        if qid not in rows:
            errs.append(f"{qid}: not in split {split}")
            continue
        if rec["split"] != split:
            errs.append(f"{qid}: split {rec['split']!r} != {split!r}")
        if rec["pipeline"] not in PIPELINES:
            errs.append(f"{qid}: bad pipeline {rec['pipeline']!r}")
        if rec["pair_id"] != rows[qid].pair_id if "pair_id" in rec else False:
            errs.append(f"{qid}: pair_id differs from data")
        if rec["error"] is not None:
            if not isinstance(rec["error"], str):
                errs.append(f"{qid}: error must be a string")
            continue  # error rows: answers may be null, counted wrong by the evaluator
        a = rec["answers"]
        if not isinstance(a, dict):
            errs.append(f"{qid}: answers null without error")
            continue
        if not isinstance(rec["latency_ms"], (int, float)) or rec["latency_ms"] < 0:
            errs.append(f"{qid}: latency_ms missing")
        for k in CORE:
            if k not in a:
                errs.append(f"{qid}: answers.{k} missing")
            else:
                _check_answer(k, a[k], CANONICAL_OPTIONS[k], errs, qid)
    gaps = sorted(set(rows) - seen)
    if gaps:
        errs.append(f"{len(gaps)} query_ids missing from log, e.g. {gaps[:5]}")
    return errs


def build_record(row, run_meta, answers, **kw):
    """Convenience for pipelines and tests: assemble a schema-conformant line (v2: three answers, no slots)."""
    rec = {
        "run_id": run_meta["run_id"], "pipeline": run_meta["pipeline"],
        "model_id": run_meta["model_id"], "model_revision": run_meta["model_revision"],
        "split": run_meta["split"], "query_id": row.query_id, "pair_id": row.pair_id,
        "answers": answers,
        "temperature_applied": None, "latency_ms": 0.0, "is_warmup": False,
        "tokens": {"input_native": None, "input_ref": None, "output_native": None, "usage_reported": None},
        "truncated": False, "tokens_dropped": 0, "error": None,
    }
    rec.update(kw)
    return rec
