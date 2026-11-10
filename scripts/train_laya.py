"""Step 4 (Kaggle GPU): fine-tune Laya-multilingual on our routing labels.

--smoke trains 1 epoch on ~120 rows: a few minutes, only to prove the format and the laya API work before the real run.
laya writes checkpoint_latest/ after every epoch and a train_report.json into --out.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so `orch` imports without install
import argparse
import json

from orch.backends import BASE_MODEL
from orch.evalkit import load_rows
from orch.laya_data import write_laya_jsonl

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="data/v2/train.jsonl")
    ap.add_argument("--eval", default="data/v2/calib.jsonl")
    ap.add_argument("--out", default="laya_ft")
    ap.add_argument("--base", default=BASE_MODEL)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    train, ev = load_rows(a.train), load_rows(a.eval)
    if a.smoke:
        train, ev, a.epochs = train[:120], ev[:40], 1
    os.makedirs(a.out, exist_ok=True)
    tr_path, ev_path = f"{a.out}_train.jsonl", f"{a.out}_eval.jsonl"
    write_laya_jsonl(train, tr_path)
    write_laya_jsonl(ev, ev_path)
    print(f"training on {len(train)} queries, evaluating on {len(ev)}, {a.epochs} epoch(s)", flush=True)

    from laya.train import TrainConfig, finetune  # installed on Kaggle only
    result = finetune(tr_path, a.base, a.out, TrainConfig(epochs=a.epochs, eval_data=ev_path, max_len=256))
    json.dump(result, open(f"{a.out}/finetune_result.json", "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in result.items() if k in ("train_items", "calibration_items", "eval_items", "skipped", "temperature", "epoch_loss")},
                     indent=1, default=str))
