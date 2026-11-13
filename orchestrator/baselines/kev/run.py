"""Kev runner (P1 steps 5-6). Writes chapter-06 logs + run.json. Resumable, one flushed line per row.

  python kev/run.py --split validation --run-id kev-0.8b-20261113-a --out runs/kev
  python kev/run.py --split validation --smoke ...        # 5 rows, one per route, written to <run-id>-smoke
  python kev/run.py --split test --limit 50 ...           # first 50 rows (pilot)

Defaults are the exact path: fp32, eager, no CUDA graphs, no fused kernels (kev.checkpoint.LoadOptions()).
"""
import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # orchestrator/baselines/
REPO = ROOT.parents[1]                  # repo root (bundle root on Kaggle): holds `orchestrator/` and `data-generation/`
sys.path.append(str(REPO))              # `orchestrator.baselines.*` (appended: upstream `kev` must win the name)

from orchestrator.baselines.kev.adapter import KevScorer           # noqa: E402
from orchestrator.baselines.common import data                 # noqa: E402
from orchestrator.baselines.common.logs import LogWriter, build_record, validate_log   # noqa: E402
from orchestrator.baselines.common.questions import QuestionConfig                     # noqa: E402
from orchestrator.baselines.common.tokens import RefTokenizer, REF_TOKENIZER_ID, REF_TOKENIZER_REVISION  # noqa: E402

WARMUP = 10  # P-03


def smoke_rows(rows):
    """First row of each gold route (5 routes)."""
    seen, out = set(), []
    for r in rows:
        route = r.support["expected_route"]
        if route not in seen:
            seen.add(route); out.append(r)
    return out


def partial_validate(path, split):
    """validate_log, minus the 'missing from log' complaint (for --smoke / --limit runs)."""
    return [e for e in validate_log(path, split) if "missing from log" not in e]


def git_sha(path):
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return None


def base_mb(ck):
    """Size of the cached base model Kev downloaded next to the adapter (None if it cannot be resolved)."""
    try:
        from huggingface_hub import snapshot_download
        return dir_mb(snapshot_download(ck.meta.base, revision=ck.meta.base_revision, local_files_only=True))
    except Exception:
        return None


def dir_mb(path):
    return round(sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file()) / 1e6, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["validation", "test"])
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", default=str(ROOT / "runs" / "kev"))
    ap.add_argument("--model", default="jaredpalmer/kev-0.8b@v1.0")
    ap.add_argument("--dtype", default="fp32", choices=["fp32", "bf16"],
                    help="load dtype; fp32 is the exact path (0.8B run). bf16 for Kev-4B on a T4 (decision C-32)")
    ap.add_argument("--shard", action="store_true",
                    help="split the bf16 backbone over all visible GPUs (Kev-9B on 2 x T4; kev/shard.py). Implies bf16")
    ap.add_argument("--kev-src", default=None, help="path of the upstream kev clone (for its git sha)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--platform", default="local")
    a = ap.parse_args()
    if a.shard:
        a.dtype = "bf16"

    import torch
    from kev.checkpoint import Checkpoint, LoadOptions

    device = "cuda" if torch.cuda.is_available() else "cpu"
    run_id = a.run_id + ("-smoke" if a.smoke else "")
    out_dir = Path(a.out) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    t = time.perf_counter()
    ck = Checkpoint(a.model)
    opts = LoadOptions() if a.dtype == "fp32" else LoadOptions(dtype=torch.bfloat16)   # None = fp32 exact path
    if a.shard:
        from orchestrator.baselines.kev.shard import load_sharded
        tok, model = load_sharded(ck)
    else:
        tok, model = ck.load(device, opts)
    load_time = time.perf_counter() - t
    if a.shard:
        from orchestrator.baselines.kev.shard import sync_all
        sync = sync_all
    else:
        sync = torch.cuda.synchronize if device == "cuda" else None
    scorer = KevScorer(tok, model, device, sync=sync)
    qconfig = QuestionConfig()
    ref = RefTokenizer()
    temperature = float(model.head.temperature)
    dtype = str(next(model.parameters()).dtype).replace("torch.", "")
    revision = Path(ck.path).name                   # HF snapshot dir name = commit hash

    meta = {"run_id": run_id, "pipeline": "kev", "model_id": a.model.split("@")[0],
            "model_revision": f"{a.model.split('@')[1] if '@' in a.model else ''}:{revision}".lstrip(":"),
            "split": a.split}

    rows = data.load_split(a.split)
    if a.smoke:
        rows = smoke_rows(rows)
    elif a.limit:
        rows = rows[:a.limit]

    log_path = out_dir / f"{a.split}.jsonl"
    started = datetime.now(timezone.utc).isoformat()
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    n_err = 0
    with LogWriter(log_path) as w:
        for i, row in enumerate(rows):
            if w.is_done(row.query_id):
                continue
            try:
                answers, st = scorer.predict(row, qconfig)
                tokens = {"input_native": st["input_native"],
                          "input_ref": ref.count_ref(st["state_text"], st["questions"]),
                          "output_native": None, "usage_reported": st["usage_reported"]}
                rec = build_record(row, meta, answers, latency_ms=st["latency_ms"], is_warmup=i < WARMUP,
                                   temperature_applied=temperature, tokens=tokens)
            except Exception as e:                  # logged, never dropped (chapter 06); counted wrong by the evaluator
                n_err += 1
                rec = build_record(row, meta, {}, latency_ms=0.0, is_warmup=i < WARMUP,
                                   temperature_applied=temperature, error=f"{type(e).__name__}: {e}"[:500])
                rec["answers"] = None
                print(f"ERROR {row.query_id}: {rec['error']}", flush=True)
            w.write(rec)
            if (i + 1) % 25 == 0:
                print(f"{i + 1}/{len(rows)}", flush=True)

    run = {
        "run_id": run_id, "pipeline": "kev", "model_id": meta["model_id"], "model_revision": meta["model_revision"],
        "dtype": dtype, "device": torch.cuda.get_device_name(0) if device == "cuda" else "cpu",
        "gpu_count": torch.cuda.device_count() if device == "cuda" else 0,
        "python": platform.python_version(),
        "libraries": {"torch": torch.__version__, "kev": git_sha(a.kev_src) if a.kev_src else None},
        "platform": a.platform, "latency_mode": "in_process",
        "question_config": f"questions.en.yaml (sha256 {qconfig.sha256})", "state_template": "p-01",
        "data_manifest_sha256": {a.split: data.manifest_sha256(a.split)},
        "load_time_s": round(load_time, 1),
        "model_size": {"params_total": sum(p.numel() for p in model.parameters()),
                       "params_method": "sum(p.numel()) over the loaded DecisionModel (base + merged LoRA + pointer head)",
                       "disk_mb_adapter": dir_mb(ck.path), "disk_mb_base": base_mb(ck),
                       "disk_mb": dir_mb(ck.path) + (base_mb(ck) or 0),
                       "peak_gpu_mem_mb": (round(sum(__import__("shard").peak_mem_mb()), 1) if a.shard else round(torch.cuda.max_memory_allocated() / 1e6, 1)) if device == "cuda" else None,
                       "peak_gpu_mem_mb_per_device": __import__("shard").peak_mem_mb() if a.shard else None,
                       "layer_split": getattr(model, "shard_map", None) if a.shard else None,
                       "peak_host_ram_mb": None},
        "temperature_applied": temperature,
        "weights_sha256": ck.weights_sha256(),
        "reference_tokenizer": f"{REF_TOKENIZER_ID}@{REF_TOKENIZER_REVISION}",
        "started_at": started, "ended_at": datetime.now(timezone.utc).isoformat(),
        "n_rows": len(rows), "n_error_rows": n_err,
        "notes": f"{'fp32 eager path (LoadOptions defaults)' if a.dtype == 'fp32' else ('bf16 load split over %d GPUs (kev/shard.py, accelerate), merged LoRA on CPU; NOT the fp32 exact path' % torch.cuda.device_count() if a.shard else 'bf16 load (LoadOptions(dtype=bfloat16)), eager, merged LoRA; NOT the fp32 exact path')}. Two calls per row (core, then predicted-feature slots); "
                 "input_native sums len(enc['ids']) over the calls (state recomputed per call).",
    }
    rj = out_dir / "run.json"
    if rj.exists():                                 # second split of the same run: keep both manifests, earliest start
        old = json.loads(rj.read_text())
        run["data_manifest_sha256"] = {**old.get("data_manifest_sha256", {}), **run["data_manifest_sha256"]}
        run["started_at"] = old.get("started_at", run["started_at"])
        run["n_rows"] = {**(old["n_rows"] if isinstance(old.get("n_rows"), dict) else {}), a.split: len(rows)}
        run["n_error_rows"] = {**(old["n_error_rows"] if isinstance(old.get("n_error_rows"), dict) else {}), a.split: n_err}
    else:
        run["n_rows"], run["n_error_rows"] = {a.split: len(rows)}, {a.split: n_err}
    rj.write_text(json.dumps(run, indent=2), encoding="utf-8")

    errs = partial_validate(log_path, a.split) if (a.smoke or a.limit) else validate_log(log_path, a.split)
    print(f"validator: {len(errs)} problem(s)")
    for e in errs[:20]:
        print("  ", e)
    print(f"rows {len(rows)} · error rows {n_err} · log {log_path}")
    sys.exit(1 if errs or n_err else 0)


if __name__ == "__main__":
    main()
