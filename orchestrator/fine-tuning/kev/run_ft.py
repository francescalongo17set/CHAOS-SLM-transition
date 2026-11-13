"""FT-P2 step 8: evaluate a fine-tuned Kev checkpoint with the UNCHANGED round-1 runner, then add the fine-tuning fields to run.json.

  python kev/run_ft.py --checkpoint runs/kev/kev-0.8b-ft-a/checkpoint --split validation --run-id kev-0.8b-ft-a \
        --out runs/kev --kev-src <upstream clone> --platform kaggle [--smoke | --limit N]

Everything after the wrapper's own flags goes to orchestrator/baselines/kev/run.py unchanged (--dtype fp32 is its default;
pass --dtype bf16 for 4B). Baselines is imported, never edited (chapter 04); run.py rewrites run.json on every call, so the
patch runs after each split. Never run on test before the configuration is frozen (FT-C-14).
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASELINES = HERE.parents[1] / "baselines"      # orchestrator/baselines in the repo and in the bundle


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_mb(p):
    return round(sum(f.stat().st_size for f in Path(p).rglob("*") if f.is_file()) / 1e6, 1)


def patch_run_json(run_json, checkpoint, train_report, temperature_json, size, train_run_id):
    rj = json.loads(Path(run_json).read_text())
    ck = Path(checkpoint)
    tr = json.loads(Path(train_report).read_text()) if Path(train_report).exists() else {}
    adapter = next(iter(sorted(ck.glob("adapter_model*.safetensors"))), None)
    rj["finetuned_from"] = {"init_from": tr.get("init_from"), "released_resolved": (tr.get("released") or {}).get("resolved"),
                            "released_weights_sha256": (tr.get("released") or {}).get("weights_sha256"),
                            "base": (tr.get("released_meta") or {}).get("base"),
                            "base_revision": (tr.get("released_meta") or {}).get("base_revision")}
    rj["train_run_id"] = train_run_id
    rj["adapter_sha256"] = sha256(adapter) if adapter else None
    rj["head_sha256"] = sha256(ck / "head.pt") if (ck / "head.pt").exists() else None
    if Path(temperature_json).exists():
        rj["temperature_fit"] = json.loads(Path(temperature_json).read_text())
    rj["training"] = {"command": tr.get("command"), "summary": tr.get("summary"), "wall_seconds": tr.get("wall_seconds"),
                      "epochs": tr.get("epochs"), "seed": tr.get("seed"), "limit": tr.get("limit"),
                      "peak_device_bytes": (tr.get("training_metrics") or {}).get("peak_device_bytes"),
                      "records_seen": (tr.get("training_metrics") or {}).get("records_seen")}
    ms = rj.get("model_size", {})
    ms["disk_mb_adapter"] = dir_mb(ck)                                  # the fine-tuned adapter folder
    if ms.get("disk_mb_base") is not None:                              # round-1 bug: 4B and 9B had null here (chapter 07)
        ms["disk_mb"] = round(ms["disk_mb_adapter"] + ms["disk_mb_base"], 1)
    rj["model_size"] = ms
    rj["notes"] = (rj.get("notes", "") + f" Fine-tuned {size} checkpoint ({train_run_id}); evaluated by baselines/kev/run.py unchanged, "
                   "fields above added by fine-tuning/kev/run_ft.py. Raw (T=1) probabilities are recoverable offline as "
                   "softmax(T * log p) with T = temperature_applied (head divides logits by T, kev/model.py PointerHead).").strip()
    Path(run_json).write_text(json.dumps(rj, indent=2), encoding="utf-8")
    return rj


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--size", default="0.8b")
    ap.add_argument("--train-run-id", default=None, help="default: the --run-id")
    a, rest = ap.parse_known_args()
    opt = argparse.ArgumentParser(allow_abbrev=False)
    for f in ("--run-id", "--out", "--split"):
        opt.add_argument(f)
    opt.add_argument("--smoke", action="store_true")
    known, _ = opt.parse_known_args(rest)
    cmd = [sys.executable, str(BASELINES / "kev" / "run.py"), "--model", a.checkpoint, *rest]
    rc = subprocess.call(cmd)
    run_dir = Path(known.out) / (known.run_id + ("-smoke" if known.smoke else ""))
    ck = Path(a.checkpoint)
    if (run_dir / "run.json").exists():
        patch_run_json(run_dir / "run.json", ck, ck.parent / "train_report.json", ck.parent / "calibration" / "temperature.json",
                       a.size, a.train_run_id or known.run_id)
        print("run.json patched:", run_dir / "run.json")
    return rc


if __name__ == "__main__":
    sys.exit(main())
