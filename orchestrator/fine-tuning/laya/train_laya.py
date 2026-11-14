"""FT-P1 step 2: fine-tune `laya-multilingual` with the `laya.train` building blocks (chapter 05, "Training script").

  python laya/train_laya.py --data-dir data/laya --out runs/laya/laya-ft-multilingual-a --limit 64 --epochs 1   # B1 smoke
  python laya/train_laya.py --data-dir data/laya --out runs/laya/laya-ft-multilingual-a --epochs 1             # B2 pilot
  python laya/train_laya.py --data-dir data/laya --out runs/laya/laya-ft-multilingual-a                        # B3 full

Not `laya.train.finetune()`: we need our own calibration file, per-epoch checkpoints and a development route macro-F1 per
epoch. Writes <out>/epochs.jsonl, <out>/train_report.json and the final checkpoint in <out>/checkpoint (laya.load reads it).

This folder has no __init__.py on purpose: a package named `laya` here would hide the installed `laya` library.
The pure helpers below do not import `laya` (unit tests need no GPU); `main()` imports it.

Development scoring: argmax of the model's logits per question, then the v2 dispatcher. A temperature is a positive scalar,
so it never changes an argmax; the route is the same as the one `predict()` would give. The harness asks all three
questions on every row, so development rows that carry no `complexity_estimation` get that question added (its label is
unused: the dispatcher reads complexity only for in-scope rows).
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]                      # repo root (bundle root on Kaggle)
sys.path[:0] = [str(REPO)]
os.environ.setdefault("USE_TF", "0")        # chapter 09: laya imports can hang with TensorFlow installed

from orchestrator.baselines.common.dispatcher import ROUTES, dispatch  # noqa: E402
from orchestrator.baselines.common.evaluate import prf  # noqa: E402

MODEL_REPO, SUBFOLDER = "convaiinnovations/laya", "multilingual"
QIDS = ("scope_check", "feature_classification", "complexity_estimation")
SANITY_ROUTE_F1 = 0.395     # FT-C-12: v2 zero-shot route macro-F1 (laya-v2-a, validation)
CONFIG = dict(epochs=4, micro_batch=8, grad_accum=8, encoder_lr=2.5e-5, head_lr=1e-4, min_lr=1e-6, loss="rlcd",
              shuffle_options=(), label_smoothing=0.0, seed=0, amp=True)


class Blocked(Exception):
    """A stop-and-ask condition of chapter 05."""


# ---------------------------------------------------------------- pure helpers (tested without laya)

def check_skipped(skipped, where):
    """Any skipped item stops the run (chapter 05, step 2)."""
    if skipped:
        raise Blocked(f"BLOCKED: {where}: items skipped by laya.train.items_from_rows: {skipped}")


def dev_route_rows(rows):
    """Development rows with all three questions in fixed order, plus the gold route of each row.

    Rows without `complexity_estimation` borrow its definition from a row that has it (identical everywhere, checked)
    and get a placeholder label that is never read. Returns (rows, gold_routes).
    """
    defs = {}
    for r in rows:
        for q, d in r["questions"].items():
            if defs.setdefault(q, d) != d:
                raise Blocked(f"BLOCKED: question {q!r} is defined differently across development rows")
    missing = [q for q in QIDS if q not in defs]
    if missing:
        raise Blocked(f"BLOCKED: development rows never define {missing}")
    out, gold = [], []
    for r in rows:
        exp = r["expected"]
        out.append({"state": r["state"], "questions": {q: defs[q] for q in QIDS},
                    "expected": {"scope_check": exp["scope_check"], "feature_classification": exp["feature_classification"],
                                 "complexity_estimation": exp.get("complexity_estimation", "simple")}})
        gold.append(dispatch(exp["scope_check"], exp["feature_classification"], exp.get("complexity_estimation")))
    return out, gold


def predict_routes(records, items, n_rows):
    """Predicted route per row from `calibration_records` output (one record per item, rows x QIDS in order)."""
    if len(items) != len(records) or len(items) != n_rows * len(QIDS):
        raise Blocked(f"BLOCKED: {len(items)} items / {len(records)} records for {n_rows} rows x {len(QIDS)} questions")
    routes = []
    for i in range(n_rows):
        lab = {}
        for j, qid in enumerate(QIDS):
            k = i * len(QIDS) + j
            logits = list(records[k][1])
            crit = list(items[k]["q"]["crit"])
            lab[qid] = crit[max(range(len(crit)), key=lambda c: logits[c])]
        routes.append(dispatch(lab["scope_check"], lab["feature_classification"], lab["complexity_estimation"]))
    return routes


def route_scores(gold, pred):
    m = prf(gold, pred, ROUTES)
    return {"route_macro_f1": m["macro_f1"], "route_accuracy": m["accuracy"], "n": m["n"]}


def select_epoch(history):
    """Best development route macro-F1 among trained epochs (epoch >= 1); the earlier epoch wins a tie."""
    trained = [h for h in history if h["epoch"] >= 1]
    if not trained:
        raise Blocked("BLOCKED: no trained epoch to select")
    return max(trained, key=lambda h: (h["route_macro_f1"], -h["epoch"]))


def check_collapse(message):
    if message:
        raise Blocked("BLOCKED: " + message)


def raw_from_calibrated(probs, t):
    """Raw (temperature 1) probabilities from calibrated ones: softmax(t * log p). Exact up to the 4-decimal rounding of
    predict() (plan open item 2)."""
    z = [t * math.log(max(p, 1e-12)) for p in probs]
    m = max(z)
    e = [math.exp(v - m) for v in z]
    s = sum(e)
    return [v / s for v in e]


def sanity_check(best_f1, floor=SANITY_ROUTE_F1):
    return {"floor": floor, "best_route_macro_f1": best_f1, "passed": best_f1 > floor}


def final_config(cfg, max_len, head_max_len, fitted):
    """Config written next to the final weights: fitted per-type temperatures, no per-bucket map carried from the base."""
    out = dict(cfg, max_len=max_len, head_max_len=head_max_len, fine_tuned=True, temperature=fitted["temperature"])
    out.pop("temperature_by_options", None)
    if fitted["temperature_by_options"]:
        out["temperature_by_options"] = fitted["temperature_by_options"]
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path, limit=0):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
                if limit and len(rows) == limit:
                    break
    return rows


def make_epoch_callback(model, score, save, history, log_path, clock=time.time):
    """`on_epoch_end(epoch, mean_loss)` for `train_model`. `score()` leaves the model in eval mode (laya's
    `calibration_records` calls `model.eval()`), so training mode is restored here: without it epochs 2+ would train with
    dropout off (B0 finding)."""
    state = {"t": clock()}

    def cb(epoch, mean_loss):
        train_s = clock() - state["t"]
        t1 = clock()
        save(epoch + 1)
        t2 = clock()
        scores = score()
        model.train()
        t3 = clock()
        row = {"epoch": epoch + 1, "mean_loss": mean_loss, "train_seconds": round(train_s, 1),
               "save_seconds": round(t2 - t1, 1), "score_seconds": round(t3 - t2, 1), **scores}
        history.append(row)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        print("epoch %d dev route macro-F1 %.4f" % (epoch + 1, scores["route_macro_f1"]), flush=True)
        state["t"] = clock()    # the next epoch's training time excludes saving and scoring

    return cb


# ---------------------------------------------------------------------------------------------- run

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True, help="folder with train / calibration / development .jsonl (data/laya)")
    ap.add_argument("--out", required=True, help="run folder, e.g. runs/laya/laya-ft-multilingual-a")
    ap.add_argument("--epochs", type=int, default=CONFIG["epochs"])
    ap.add_argument("--limit", type=int, default=0, help="first N train rows only (smoke, pilot)")
    ap.add_argument("--dev-limit", type=int, default=0, help="first N development rows only (smoke)")
    ap.add_argument("--seed", type=int, default=CONFIG["seed"])
    ap.add_argument("--keep-epochs", action="store_true", help="keep every epoch folder (default: only the selected one)")
    ap.add_argument("--no-sanity", action="store_true", help="smoke and pilot: skip the FT-C-12 floor")
    ap.add_argument("--revision", default=None, help="Hub revision to start from (default: current head, recorded)")
    ap.add_argument("--device", default="auto")
    a = ap.parse_args()

    import torch
    import laya
    import laya.train as LT
    from huggingface_hub import HfApi, snapshot_download

    out = Path(a.out)
    if (out / "checkpoint").exists():
        print(f"BLOCKED: {out / 'checkpoint'} exists (an earlier run). Smoke and pilot runs are cleared by the notebook; a full run needs a new run id.")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    epochs_log = out / "epochs.jsonl"
    epochs_log.write_text("")
    data = Path(a.data_dir)
    t_start = time.time()
    dev = LT.resolve_device(a.device)

    revision = a.revision or HfApi().model_info(MODEL_REPO).sha
    root = snapshot_download(MODEL_REPO, revision=revision, allow_patterns=[
        f"{SUBFOLDER}/{n}" for n in ("rl_agent_config.json", "model.safetensors", "tokenizer/*", "encoder/*")])
    model, tok, cfg = LT.load_checkpoint(os.path.join(root, SUBFOLDER))
    max_len, head_max_len = cfg["max_len"], cfg["head_max_len"]
    if (max_len, head_max_len) != (1024, 256):
        raise Blocked(f"BLOCKED: multilingual config max_len/head_max_len = {max_len}/{head_max_len}, expected 1024/256")

    train_rows = read_rows(data / "train.jsonl", a.limit)
    calib_rows = read_rows(data / "calibration.jsonl")
    dev_rows, gold = dev_route_rows(read_rows(data / "development.jsonl", a.dev_limit))
    train_items, sk_train = LT.items_from_rows(tok, train_rows, max_len, head_max_len, label_smoothing=CONFIG["label_smoothing"])
    calib_items, sk_calib = LT.items_from_rows(tok, calib_rows, max_len, head_max_len)
    dev_items, sk_dev = LT.items_from_rows(tok, dev_rows, max_len, head_max_len)
    skipped = {"train": sk_train, "calibration": sk_calib, "development": sk_dev}
    for name, sk in skipped.items():
        check_skipped(sk, name)
    print(f"train items {len(train_items)}, calibration items {len(calib_items)}, development items {len(dev_items)} "
          f"({len(dev_rows)} rows), device {dev}", flush=True)

    config = LT.TrainConfig(**{**CONFIG, "epochs": a.epochs, "seed": a.seed})
    print(LT.update_budget_message(len(train_items), config), flush=True)
    model.to(dev)

    def score():
        recs = LT.calibration_records(model, tok, dev_items, dev, max_len, head_max_len)
        return route_scores(gold, predict_routes(recs, dev_items, len(dev_rows)))

    def save(epoch):
        LT.save_checkpoint(model, tok, dict(cfg, max_len=max_len, head_max_len=head_max_len), str(out / f"epoch_{epoch}"))

    base = score()                      # epoch 0: the starting checkpoint, same scorer
    history = [{"epoch": 0, "mean_loss": None, **base}]
    epochs_log.write_text(json.dumps(history[0]) + "\n")
    print("epoch 0 (start) dev route macro-F1 %.4f" % base["route_macro_f1"], flush=True)

    if dev.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
    cb = make_epoch_callback(model, score, save, history, epochs_log)
    t0 = time.time()
    losses = LT.train_model(model, tok, train_items, config, dev, max_len, head_max_len, on_epoch_end=cb)
    train_wall = time.time() - t0
    peak_mem = round(torch.cuda.max_memory_allocated() / 2**20, 1) if dev.type == "cuda" else None

    best = select_epoch(history)
    print("selected epoch", best["epoch"], "route macro-F1 %.4f" % best["route_macro_f1"], flush=True)
    del model
    if dev.type == "cuda":
        torch.cuda.empty_cache()
    # Calibrate on the saved (fp16) weights of the selected epoch: the weights the evaluation harness will load.
    model, tok, _ = LT.load_checkpoint(str(out / f"epoch_{best['epoch']}"))
    model.to(dev)
    records = LT.calibration_records(model, tok, calib_items, dev, max_len, head_max_len)
    check_collapse(LT.prior_collapse_message(records))
    fitted = LT.fit_temperature_map(records)
    calibration = LT.calibration_report(records, fitted["temperature"])
    stats = LT.collapse_stats(records)
    final = out / "checkpoint"
    LT.save_checkpoint(model, tok, final_config(cfg, max_len, head_max_len, fitted), str(final))

    if not a.keep_epochs:
        for h in history:
            if h["epoch"] not in (0, best["epoch"]):
                shutil.rmtree(out / f"epoch_{h['epoch']}", ignore_errors=True)
    shutil.rmtree(out / f"epoch_{best['epoch']}", ignore_errors=True)   # identical weights live in checkpoint/

    sanity = None if a.no_sanity else sanity_check(best["route_macro_f1"])
    report = {
        "run_note": "FT-P1 train_laya.py", "model": f"{MODEL_REPO}/{SUBFOLDER}", "revision": revision,
        "laya_version": laya.__version__, "torch_version": torch.__version__,
        "device": torch.cuda.get_device_name(0) if dev.type == "cuda" else str(dev),
        "config": {**CONFIG, "epochs": a.epochs, "seed": a.seed, "shuffle_options": []},
        "limits": {"train_rows": a.limit, "dev_rows": a.dev_limit},
        "items": {"train": len(train_items), "calibration": len(calib_items), "development": len(dev_items)},
        "skipped": skipped, "max_len": max_len, "head_max_len": head_max_len,
        "epoch_mean_loss": losses, "epochs": history, "epoch_selected": best["epoch"],
        "temperature": fitted["temperature"], "temperature_by_options": fitted["temperature_by_options"],
        "temperature_clamped": fitted["temperature_clamped"], "n_by_bucket": fitted["n_by_bucket"],
        "calibration": calibration, "collapse_stats": stats,
        "weights_sha256": sha256(final / "model.safetensors"),
        "train_wall_seconds": round(train_wall, 1), "total_wall_seconds": round(time.time() - t_start, 1),
        "peak_gpu_mem_mb": peak_mem, "sanity": sanity,
        "note": "development route macro-F1 from argmax of fp32 logits + v2 dispatcher; the selected epoch is calibrated "
                "and scored from its fp16 checkpoint, the weights the harness loads.",
    }
    (out / "train_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if sanity and not sanity["passed"]:
        print(f"BLOCKED: sanity check failed: best development route macro-F1 {best['route_macro_f1']:.4f} <= {SANITY_ROUTE_F1} (FT-C-12)")
        return 3
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Blocked as e:
        print(e)
        sys.exit(2)
