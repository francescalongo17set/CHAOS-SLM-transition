"""FT-P1 step 3: evaluate a fine-tuned Laya checkpoint folder with the round-1 harness, then add the fine-tuning fields to run.json.

  python laya/run_ft_laya.py --checkpoint runs/laya/laya-ft-multilingual-a/checkpoint --run-id laya-ft-multilingual-a \
        --out runs/laya --split validation            # test only after FT-C-14 (FROZEN)
  python laya/run_ft_laya.py ... --smoke | --limit N    # partial runs, numbers go to the run.json notes

Plan open item 1: baselines/laya/run_laya.py loads from the Hub and has no --checkpoint option, and baselines are never
edited. This script replaces only `load_agent` (`laya.load(<dir>)`, fails if another checkpoint is loaded) and reuses
`run_split`, `run_meta`, `summary`, the adapter and the log writer by import. The per-row log field `temperature_applied` stays
null (Laya hides it); the fitted temperatures are in run.json instead, so raw probabilities are recoverable offline as
softmax(T * log p) (plan open item 2).

No __init__.py in this folder on purpose: a package named `laya` here would hide the installed `laya` library.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASELINES = HERE.parents[1] / "baselines"          # orchestrator/baselines in the repo and in the bundle
REPO = HERE.parents[2]
sys.path[:0] = [str(REPO)]
os.environ.setdefault("USE_TF", "0")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_mb(p):
    return round(sum(f.stat().st_size for f in Path(p).rglob("*") if f.is_file()) / 1e6, 1)


def verify_loaded(agent, checkpoint):
    """Fail if the agent is not the requested folder, not fine-tuned, or does not carry the folder's own temperatures."""
    ck = Path(checkpoint).resolve()
    cfg = json.loads((ck / "rl_agent_config.json").read_text())
    problems = []
    if Path(str(agent.model_id)).resolve() != ck:
        problems.append(f"loaded {agent.model_id!r}, requested {str(ck)!r}")
    if not cfg.get("fine_tuned"):
        problems.append("checkpoint config has no fine_tuned flag")
    if list(agent.temperature_raw) != list(cfg["temperature"]):
        problems.append(f"agent temperatures {list(agent.temperature_raw)} != checkpoint {cfg['temperature']}")
    if dict(agent.temperature_by_options_raw) != dict(cfg.get("temperature_by_options") or {}):
        problems.append("agent per-bucket temperatures differ from the checkpoint's")
    if problems:
        raise SystemExit("BLOCKED: " + "; ".join(problems))
    return cfg


def ft_identity(train_report, weights_sha, train_run_id):
    """(model_id, model_revision) written into every log row and run.json, fixed before the first row is logged."""
    tr = json.loads(Path(train_report).read_text()) if Path(train_report).exists() else {}
    return (f"{tr.get('model', 'convaiinnovations/laya/multilingual')} fine-tuned ({train_run_id})", f"ft:{weights_sha[:16]}")


def patch_run_json(run_json, checkpoint, train_report, train_run_id, kaggle_dataset=None):
    """Add the fine-tuning fields (chapter 03) to a run.json written by the baselines runner. Idempotent."""
    rj = json.loads(Path(run_json).read_text())
    ck = Path(checkpoint)
    tr = json.loads(Path(train_report).read_text()) if Path(train_report).exists() else {}
    weights = ck / "model.safetensors"
    rj["finetuned_from"] = {"model": tr.get("model"), "revision": tr.get("revision")}
    rj["train_run_id"] = train_run_id
    rj["weights_sha256"] = sha256(weights) if weights.exists() else None
    rj["kaggle_dataset"] = kaggle_dataset
    rj["epoch_selected"] = tr.get("epoch_selected")
    rj["temperature_fit"] = {"temperature": tr.get("temperature"), "temperature_by_options": tr.get("temperature_by_options"),
                             "temperature_clamped": tr.get("temperature_clamped"), "n_by_bucket": tr.get("n_by_bucket"),
                             "calibration_items": (tr.get("items") or {}).get("calibration")}
    rj["training"] = {"config": tr.get("config"), "limits": tr.get("limits"), "items": tr.get("items"),
                      "epoch_mean_loss": tr.get("epoch_mean_loss"), "epochs": tr.get("epochs"),
                      "train_wall_seconds": tr.get("train_wall_seconds"), "peak_gpu_mem_mb": tr.get("peak_gpu_mem_mb"),
                      "sanity": tr.get("sanity")}
    ms = rj.get("model_size", {})
    ms["disk_mb"] = dir_mb(ck)
    rj["model_size"] = ms
    if rj["weights_sha256"]:
        rj["model_id"], rj["model_revision"] = ft_identity(train_report, rj["weights_sha256"], train_run_id)
    note = (" Fine-tuned checkpoint evaluated by baselines/laya/run_laya.py code unchanged (run_split, run_meta) through "
            "fine-tuning/laya/run_ft_laya.py. Probabilities as logged are calibrated with temperature_fit.temperature "
            "(per question type; the per-bucket map is empty); raw (T=1) probabilities are recoverable offline as "
            "softmax(T * log p), up to the 4-decimal rounding of predict(). temperature_applied stays null per row.")
    if note.strip() not in rj.get("notes", ""):
        rj["notes"] = (rj.get("notes", "") + note).strip()
    Path(run_json).write_text(json.dumps(rj, indent=2, ensure_ascii=False), encoding="utf-8")
    return rj


def load_baseline_runner():
    spec = importlib.util.spec_from_file_location("run_laya_baseline", BASELINES / "laya" / "run_laya.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--checkpoint", required=True, help="folder written by train_laya.py (runs/laya/<id>/checkpoint)")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--train-run-id", default=None, help="default: --run-id")
    ap.add_argument("--kaggle-dataset", default=None, help="name of the private Dataset holding the checkpoint (FT-P-06)")
    ap.add_argument("--split", nargs="+", default=["validation"], choices=["validation", "test"])
    ap.add_argument("--smoke", action="store_true", help="4 validation rows, one per route")
    ap.add_argument("--limit", type=int, help="first N rows of each split (pilot)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default=None)
    a = ap.parse_args()

    R = load_baseline_runner()
    import laya
    import torch
    from orchestrator.baselines.common import data
    from orchestrator.baselines.common.evaluate import evaluate
    from orchestrator.baselines.common.logs import validate_log
    from orchestrator.baselines.common.questions import QuestionConfig
    from orchestrator.baselines.common.report import write_report
    from orchestrator.baselines.common.tokens import RefTokenizer
    import orchestrator.baselines.laya.laya_adapter as A

    ck = Path(a.checkpoint).resolve()
    train_report = ck.parent / "train_report.json"
    splits = ["validation"] if a.smoke else a.split
    partial = a.smoke or a.limit is not None
    run_dir = Path(a.out) / (a.run_id + ("-smoke" if a.smoke else ""))
    run_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    agent = laya.load(str(ck), device=a.device)
    load_s = time.perf_counter() - t0
    verify_loaded(agent, ck)
    qcfg, ref = QuestionConfig(), RefTokenizer()
    weights_sha = sha256(ck / "model.safetensors")
    meta = R.run_meta(agent, weights_sha, load_s, 0, qcfg, splits, a.run_id)
    meta["model_id"], meta["model_revision"] = ft_identity(train_report, weights_sha, a.train_run_id or a.run_id)
    meta_file = run_dir / "run.json"
    if meta_file.exists():                       # resumed run: same weights, keep the original start
        old = json.loads(meta_file.read_text())
        if old.get("weights_sha256") and old["weights_sha256"] != weights_sha:
            sys.exit(f"BLOCKED: {a.run_id} was started with other weights (sha256 differs)")
        meta["started_at"] = old["started_at"]

    notes = []
    for split in splits:
        rows = data.load_split(split)
        rows = A.route_rows(rows) if a.smoke else rows[:a.limit] if a.limit else rows
        log = R.run_split(agent, qcfg, ref, meta, split, rows, run_dir)
        if torch.cuda.is_available():
            meta["model_size"]["peak_gpu_mem_mb"] = round(torch.cuda.max_memory_allocated() / 2**20, 1)
        meta["ended_at"] = R.now()
        if partial:
            notes.append(R.summary(log))
            meta["notes"] = meta["notes"].split(" | ")[0] + " | " + " ".join(notes)
        meta_file.write_text(json.dumps(meta, indent=1, ensure_ascii=False))
        patch_run_json(meta_file, ck, train_report, a.train_run_id or a.run_id, a.kaggle_dataset)
        if partial:
            print(notes[-1])
            continue
        errs = validate_log(log, split)
        if errs:
            sys.exit(f"{split}: log not accepted ({len(errs)} problems), first: {errs[:5]}")
        M = evaluate(log, split, run_json=meta_file, out_dir=run_dir)
        write_report(M, run_dir / f"report_{split}.md")
        patch_run_json(meta_file, ck, train_report, a.train_run_id or a.run_id, a.kaggle_dataset)   # evaluate may rewrite run.json
        meta = json.loads(meta_file.read_text())
        print(f"{split}: done, route accuracy {M['route']['accuracy']:.3f}, error rows {M['n_error_rows']}")
    print("run.json:", meta_file)


if __name__ == "__main__":
    main()
