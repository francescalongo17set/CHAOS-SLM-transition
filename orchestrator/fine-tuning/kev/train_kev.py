"""FT-P2 step 2: warm-start fine-tune of a released Kev checkpoint with `python -m kev.train` (chapter 06).

  python kev/train_kev.py --size 0.8b --data-dir data/kev --out runs/kev/kev-0.8b-ft-a --dry-run     # print the command only
  python kev/train_kev.py --size 0.8b --data-dir data/kev --out runs/kev/kev-0.8b-ft-a --limit 32 --max-steps 1   # C1 smoke
  python kev/train_kev.py --size 0.8b --data-dir data/kev --out runs/kev/kev-0.8b-ft-a --limit 300              # C2 pilot
  python kev/train_kev.py --size 0.8b --data-dir data/kev --out runs/kev/kev-0.8b-ft-a                          # C3 full

Architecture arguments are copied from the released checkpoint's meta, never from kev.train defaults. This folder has no
__init__.py and must never shadow the upstream `kev` package. Needs upstream kev (torch) installed, except for --dry-run
with --meta-json (tests). Writes <out>/train_report.json; the checkpoint goes to <out>/checkpoint.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

LR_CAP = 5e-5       # kev_modal.py MAX_DELTA_LR: released deltas used 2e-5..4e-5, kev.train's default 2e-4 is for scratch training
SIZES = {
    "0.8b": {"init_from": "jaredpalmer/kev-0.8b@9a45d25eb2ab761841196625383fa1dff0e56c1e", "dtype": "fp32", "weights_dtype": "fp32",
             "checkpointing": 0, "sanity_macro_f1": 0.357, "box_hours": 2},
    # 4B revision: baselines C-32 gives the short hash 139fdd94; resolve it to the full commit in session before use (chapter 09)
    "4b": {"init_from": "jaredpalmer/kev-4b@139fdd94", "dtype": "bf16", "weights_dtype": "bf16",
           "checkpointing": 1, "sanity_macro_f1": 0.483, "box_hours": 3},
}
ARCH_KEYS = ("base", "base_revision", "lora", "head_dim", "option_isolation", "special_embeddings", "weights_dtype", "weights")


def meta_to_dict(meta):
    return {"base": meta.base, "base_revision": meta.base_revision, "lora": meta.lora, "head_dim": meta.head_dim,
            "option_isolation": bool(meta.option_isolation), "special_embeddings": bool(meta.special_embeddings),
            "weights_dtype": meta.weights_dtype, "weights": meta.weights, "temperature": meta.temperature,
            "extra_args": dict(meta.extra.get("args") or {})}


def build_command(meta, cfg, data, out, epochs=1, seed=0, max_steps=0, python=sys.executable):
    """meta: dict from meta_to_dict. cfg: SIZES entry. Returns (argv list of str, summary dict). Raises on anything unexpected."""
    if meta["weights"] != "lora":
        raise ValueError(f"released checkpoint has weights={meta['weights']!r}; this recipe trains LoRA only")
    if meta["weights_dtype"] != cfg["weights_dtype"]:           # warm_start does not compare weights_dtype: we do
        raise ValueError(f"meta weights_dtype {meta['weights_dtype']!r} != configured {cfg['weights_dtype']!r}: stop and ask")
    margs = meta["extra_args"]
    for k in ("lr", "lora_targets"):
        if k not in margs:
            raise ValueError(f"released meta.extra['args'] has no {k!r}: stop and ask (keys: {sorted(margs)})")
    lr = min(float(margs["lr"]), LR_CAP)
    cmd = [python, "-m", "kev.train", "--data", data, "--init_from", cfg["init_from"], "--out", out,
           "--device", "cuda", "--dtype", cfg["dtype"], "--weights_dtype", cfg["weights_dtype"],
           "--checkpointing", cfg["checkpointing"],
           "--base", meta["base"], "--lora", meta["lora"], "--head_dim", meta["head_dim"], "--lora_targets", margs["lora_targets"],
           "--option_isolation", int(meta["option_isolation"]), "--special_embeddings", int(meta["special_embeddings"]),
           "--lr", lr, "--epochs", epochs, "--batch", 1, "--accum", 8, "--p_none_pair", 0.25, "--seed", seed]
    if meta["base_revision"]:
        cmd += ["--base_revision", meta["base_revision"]]
    if max_steps:
        cmd += ["--max_steps", max_steps]
    summary = {"lr": lr, "meta_lr": margs["lr"], "lr_cap": LR_CAP, "released_args": margs,
               "differs_from_released": {k: [margs[k], v] for k, v in (("batch", 1), ("accum", 8), ("checkpointing", cfg["checkpointing"]))
                                         if k in margs and margs[k] != v}}
    return [str(c) for c in cmd], summary


def limit_file(src, n, dst):
    with open(src, encoding="utf-8") as f, open(dst, "w", encoding="utf-8", newline="\n") as g:
        k = 0
        for line in f:
            if line.strip():
                g.write(line); k += 1
                if k == n:
                    break
    return k


def count_dropped(data_path, meta_base, base_revision, max_state=None):
    """Zero drops allowed (chapter 06): kev.train only prints a message when it drops a record. Needs torch + kev."""
    from kev.data import load_records, materialize
    from kev.model import fits, load_tokenizer
    from kev.train import MAX_STATE, training_context
    tok = load_tokenizer(meta_base, revision=base_revision)
    ctx = training_context(max_state or MAX_STATE)
    recs = load_records(data_path)
    return [r["_meta"]["id"] for r in recs if not fits(materialize(r), tok, **ctx)], len(recs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", required=True, choices=list(SIZES))
    ap.add_argument("--data-dir", required=True, help="folder with train.jsonl (data/kev)")
    ap.add_argument("--out", required=True, help="run folder, e.g. runs/kev/kev-0.8b-ft-a (must not exist for a real run)")
    ap.add_argument("--init-from", default=None, help="override the pinned released checkpoint (default: the size's pin)")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0, help="first N records only (smoke, pilot)")
    ap.add_argument("--max-steps", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--meta-json", default=None, help="tests: a meta dict (meta_to_dict form) instead of reading the checkpoint")
    ap.add_argument("--allow-drop", action="store_true", help="NOT for real runs: continue although kev.model.fits drops records")
    a = ap.parse_args()
    cfg = dict(SIZES[a.size])
    if a.init_from:
        cfg["init_from"] = a.init_from
    out = Path(a.out)
    data = Path(a.data_dir) / "train.jsonl"

    if a.meta_json:
        meta = json.loads(Path(a.meta_json).read_text())
        released = {"resolved": None, "weights_sha256": None}
    else:
        from kev.checkpoint import Checkpoint
        ck = Checkpoint(cfg["init_from"])
        meta, released = meta_to_dict(ck.meta), {"resolved": ck.path, "weights_sha256": ck.weights_sha256()}
    print("released meta:", json.dumps({k: meta[k] for k in (*ARCH_KEYS, "temperature")}), "\nreleased args:", json.dumps(meta["extra_args"]))

    train_path = data
    if a.limit and not a.dry_run:
        out.mkdir(parents=True, exist_ok=True)
        train_path = out / f"train_first{a.limit}.jsonl"
        limit_file(data, a.limit, train_path)
    cmd, summary = build_command(meta, cfg, str(train_path), str(out / "checkpoint"), a.epochs, a.seed, a.max_steps)
    print("command:", " ".join(cmd))
    if a.dry_run:
        return 0

    if not a.meta_json:
        dropped, n = count_dropped(train_path, meta["base"], meta["base_revision"])
        print(f"records {n}, dropped by kev.model.fits: {len(dropped)}")
        if dropped and not a.allow_drop:
            print(f"BLOCKED: {len(dropped)} records exceed Kev's training context (e.g. {dropped[:5]}); zero drops allowed")
            return 2
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    log = out / "train.log"
    dropped_msg = None
    with open(log, "w", encoding="utf-8") as lf:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            print(line, end="", flush=True); lf.write(line)
            if re.match(r"dropped \d+ of", line):
                dropped_msg = line.strip()
        rc = p.wait()
    wall = time.time() - t0
    report = {"size": a.size, "init_from": cfg["init_from"], "released": released, "released_meta": meta, "command": cmd,
              "summary": summary, "limit": a.limit, "max_steps": a.max_steps, "epochs": a.epochs, "seed": a.seed,
              "wall_seconds": round(wall, 1), "return_code": rc, "dropped_message": dropped_msg,
              "training_metrics": None, "checkpoint_check": None}
    for cand in (out / "checkpoint" / "training_metrics.json", out / "training_metrics.json"):
        if cand.exists():
            report["training_metrics"] = json.loads(cand.read_text())
            break
    if rc == 0 and not a.meta_json:
        from kev.checkpoint import read_meta
        new = read_meta(str(out / "checkpoint"))
        same = {k: [getattr(new, k), meta[k]] for k in ARCH_KEYS if getattr(new, k) != meta[k]}
        report["checkpoint_check"] = {"base_revision": new.base_revision, "architecture_differences": same,
                                      "temperature_after_training": new.temperature,
                                      "init_source": new.extra.get("init_source")}
        if same:
            print("BLOCKED: architecture differs from the released checkpoint:", same)
            rc = 3
    (out / "train_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if dropped_msg and not a.allow_drop:
        print("BLOCKED:", dropped_msg); rc = rc or 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
