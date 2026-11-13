"""Laya runs (plan P2, handbook chapter 09). Resumable; one log line per row (chapter 06).

From orchestrator-baselines/:
    python laya/run_laya.py --run-id laya-a-smoke --smoke                       # 5 rows, one per route
    python laya/run_laya.py --run-id laya-a-pilot --split validation --limit 50  # pilot
    python laya/run_laya.py --run-id laya-a                                     # full validation + test

Outputs in runs/laya/<run_id>/: <split>.jsonl and run.json; full runs also get the shared
report_<split>.md, metrics_<split>.json and confusion_*.csv. Smoke and pilot runs are partial,
which the shared validator rejects, so their numbers go to the run.json notes instead.
"""
import argparse
import datetime as dt
import json
import os
import platform
import resource
import statistics
import sys
import time
from pathlib import Path

from orchestrator.baselines.common import data

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE), str(ROOT)]
os.environ.setdefault("USE_TF", "0")  # chapter 09: laya.load() can hang with TensorFlow installed

import laya  # noqa: E402  (the installed library: laya/ here has no __init__.py)
import torch  # noqa: E402
import transformers  # noqa: E402
from huggingface_hub import HfApi  # noqa: E402

import orchestrator.baselines.laya.laya_adapter as A  # noqa: E402
from orchestrator.baselines.common import state  # noqa: E402
from orchestrator.baselines.common.evaluate import evaluate  # noqa: E402
from orchestrator.baselines.common.logs import LogWriter, read_log, validate_log  # noqa: E402
from orchestrator.baselines.common.questions import QuestionConfig  # noqa: E402
from orchestrator.baselines.common.report import write_report  # noqa: E402
from orchestrator.baselines.common.tokens import RefTokenizer  # noqa: E402

MODEL_REPO, SUBFOLDER = "convaiinnovations/laya", "multilingual"  # C-05, chapter 09
WARMUP = 10  # P-03
DTYPES = {torch.float16: "fp16", torch.bfloat16: "bf16", torch.float32: "fp32"}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def load_agent(device):
    info = HfApi().model_info(MODEL_REPO, files_metadata=True)  # pin the revision used
    t0 = time.perf_counter()
    agent = laya.load(MODEL_REPO, subfolder=SUBFOLDER, revision=info.sha, device=device)
    load_s = time.perf_counter() - t0
    if getattr(agent, "subfolder", None) != SUBFOLDER:  # chapter 09: multilingual for every row
        sys.exit(f"BLOCKED: loaded subfolder {getattr(agent, 'subfolder', None)!r}, expected {SUBFOLDER!r}")
    disk = sum(s.size or 0 for s in info.siblings if s.rfilename.startswith(SUBFOLDER + "/"))
    return agent, info.sha, load_s, disk


def run_meta(agent, revision, load_s, disk, qcfg, splits, run_id):
    cuda = torch.cuda.is_available()
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # KB on Linux, bytes on macOS
    return {
        "run_id": run_id, "pipeline": "laya", "model_id": f"{MODEL_REPO}/{SUBFOLDER}",
        "model_revision": agent.revision or revision,
        "dtype": DTYPES.get(agent.dtype_for(3), str(agent.dtype_for(3))),
        "device": torch.cuda.get_device_name(0) if cuda else str(agent.device),
        "gpu_count": torch.cuda.device_count() if cuda else 0,
        "python": platform.python_version(),
        "libraries": {"laya": laya.__version__, "torch": torch.__version__,
                      "transformers": transformers.__version__},
        "platform": ("kaggle" if os.environ.get("KAGGLE_KERNEL_RUN_TYPE")
                     else "colab" if os.environ.get("COLAB_RELEASE_TAG") else "local"),
        "latency_mode": "in_process",
        "question_config": f"questions.en.yaml (sha256 {qcfg.sha256})",
        "state_template": "p-01",
        "data_manifest_sha256": {s: data.manifest_sha256(s) for s in splits},
        "load_time_s": round(load_s, 2),
        "model_size": {
            "params_total": sum(p.numel() for p in agent.model.parameters()),
            "params_method": "sum of numel over agent.model.parameters() (encoder + decision head)",
            "disk_mb": round(disk / 1e6, 1),
            "peak_gpu_mem_mb": round(torch.cuda.max_memory_allocated() / 2**20, 1) if cuda else None,
            "peak_host_ram_mb": round(rss / (2**20 if sys.platform == "darwin" else 2**10), 1)},
        "max_len": agent.cfg.get("max_len"), "head_max_len": agent.cfg.get("head_max_len"),
        "started_at": now(), "ended_at": None,
        "notes": ("Two predict() calls per row (C-23): scope/feature/complexity, then the slots of the "
                  "predicted feature; latency_ms and input_native are the sum of both. input_native is "
                  "Laya's usage.input_tokens. Probabilities as shipped: Laya applies the checkpoint's "
                  "temperatures inside predict() and does not report them, so temperature_applied is null."),
    }


def summary(log):
    """Latency, tokens and errors of a partial (smoke / pilot) log, for the run.json notes."""
    recs = read_log(log)
    ok = [r for r in recs if r["error"] is None]
    lat = [r["latency_ms"] for r in ok if not r["is_warmup"]] or [r["latency_ms"] for r in ok]
    tok = [r["tokens"]["input_native"] for r in ok]
    return (f"{log.stem}: {len(recs)} rows, {len(recs) - len(ok)} errors, "
            f"{sum(1 for r in ok if r['truncated'])} truncated; latency_ms median "
            f"{statistics.median(lat) if lat else None} over {len(lat)} rows; input_native mean "
            f"{statistics.mean(tok) if tok else None}.")


def run_split(agent, qcfg, ref, meta, split, rows, run_dir):
    log = run_dir / f"{split}.jsonl"
    rmeta = dict(meta, split=split)
    with LogWriter(log) as w:
        for i, row in enumerate(rows):
            if w.is_done(row.query_id):
                continue
            st = state.serialize_state(row.model_input)
            t0 = time.perf_counter()
            try:
                core, slot_qs, ra, rb = A.predict_row(agent, qcfg, st)
                ms = (time.perf_counter() - t0) * 1000  # results are CPU floats: GPU work is done
                rec = A.make_record(row, rmeta, core, slot_qs, ra, rb, ms, i < WARMUP,
                                    ref.count_ref(st, core + slot_qs))
            except Exception as e:  # noqa: BLE001  chapter 06: log failed rows, never drop them
                rec = A.error_record(row, rmeta, f"{type(e).__name__}: {e}",
                                     (time.perf_counter() - t0) * 1000, i < WARMUP)
            w.write(rec)
            if (i + 1) % 50 == 0:
                print(f"{split}: {i + 1}/{len(rows)}", flush=True)
    return log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True, help="stable id; rerun with it to resume")
    ap.add_argument("--split", nargs="+", default=["validation", "test"], choices=["validation", "test"])
    ap.add_argument("--smoke", action="store_true", help="5 validation rows, one per route")
    ap.add_argument("--limit", type=int, help="first N rows of each split (pilot)")
    ap.add_argument("--out", default=str(ROOT / "runs" / "laya"))
    ap.add_argument("--device", default=None, help="passed to laya.load (default: laya's choice)")
    a = ap.parse_args()
    splits = ["validation"] if a.smoke else a.split
    partial = a.smoke or a.limit is not None

    run_dir = Path(a.out) / a.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    qcfg, ref = QuestionConfig(), RefTokenizer()
    agent, revision, load_s, disk = load_agent(a.device)
    meta = run_meta(agent, revision, load_s, disk, qcfg, splits, a.run_id)
    meta_file = run_dir / "run.json"
    if meta_file.exists():  # resumed run: same model revision, keep the original start
        old = json.loads(meta_file.read_text())
        if old["model_revision"] != meta["model_revision"]:
            sys.exit(f"BLOCKED: {a.run_id} used revision {old['model_revision']}, now {meta['model_revision']}")
        meta["started_at"] = old["started_at"]

    notes = []
    for split in splits:
        rows = data.load_split(split)
        rows = A.route_rows(rows) if a.smoke else rows[:a.limit] if a.limit else rows
        log = run_split(agent, qcfg, ref, meta, split, rows, run_dir)
        if torch.cuda.is_available():
            meta["model_size"]["peak_gpu_mem_mb"] = round(torch.cuda.max_memory_allocated() / 2**20, 1)
        meta["ended_at"] = now()
        if partial:
            notes.append(summary(log))
            meta["notes"] = meta["notes"].split(" | ")[0] + " | " + " ".join(notes)
        meta_file.write_text(json.dumps(meta, indent=1, ensure_ascii=False))
        if partial:
            print(notes[-1])
            continue
        errs = validate_log(log, split)
        if errs:
            sys.exit(f"{split}: log not accepted ({len(errs)} problems), first: {errs[:5]}")
        M = evaluate(log, split, run_json=meta_file, out_dir=run_dir)
        write_report(M, run_dir / f"report_{split}.md")
        print(f"{split}: done, route accuracy {M['route']['accuracy']:.3f}, error rows {M['n_error_rows']}")


if __name__ == "__main__":
    main()
