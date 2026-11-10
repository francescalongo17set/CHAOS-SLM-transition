"""Step 3: split the generated queries into train / calibration / test by SOURCE FAMILY, and carve the hand-check gold set.

All queries written from the same law article (or the same topic) land in the same split, so the test set contains
passages and topics the model never saw in training. Gold = 50 items sampled from test, as an editable CSV.
Outputs in --out: train.jsonl, calib.jsonl, test.jsonl, gold.csv (subset of test), manifest.json
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so `orch` imports without install
import argparse
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict

from orch.evalkit import sha256

COLS = ["id", "query", "language", "scope", "complexity", "safety", "cell", "source", "verified", "notes"]


def split_of(family: str, seed: int, train=0.70, calib=0.15) -> str:
    """Deterministic: the same family always gets the same split, whatever else is in the file."""
    x = int(hashlib.sha256(f"{seed}|{family}".encode()).hexdigest(), 16) % 10_000 / 10_000
    return "train" if x < train else "calib" if x < train + calib else "test"


def family_of(row) -> str:
    return row["source"].split("; ")[0]


def stratified_gold(rows, k, seed):
    """k items spread over generation cells in proportion to cell size (largest remainder), random within a cell."""
    by = defaultdict(list)
    for r in rows:
        by[r["cell"]].append(r)
    rng = random.Random(seed)
    quota = {c: k * len(v) / len(rows) for c, v in by.items()}
    take = {c: int(q) for c, q in quota.items()}
    for c in sorted(quota, key=lambda c: quota[c] - take[c], reverse=True)[: k - sum(take.values())]:
        take[c] += 1
    gold = []
    for c, v in sorted(by.items()):
        v = v[:]
        rng.shuffle(v)
        gold += v[: take[c]]
    return gold


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", default="data/gen/queries.jsonl")
    ap.add_argument("--out", default="data/v2")
    ap.add_argument("--gold-size", type=int, default=50)
    ap.add_argument("--seed", type=int, default=13)
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.queries, encoding="utf-8")]
    parts = defaultdict(list)
    for r in rows:
        parts[split_of(family_of(r), a.seed)].append(r)
    os.makedirs(a.out, exist_ok=True)
    for name in ("train", "calib", "test"):
        write_jsonl(f"{a.out}/{name}.jsonl", parts[name])
    gold = stratified_gold(parts["test"], min(a.gold_size, len(parts["test"])), a.seed)
    with open(f"{a.out}/gold.csv", "w", encoding="utf-8-sig", newline="") as f:  # BOM so Excel shows accents correctly
        w = csv.DictWriter(f, COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(gold, key=lambda r: r["id"]))
    manifest = {"version": os.path.basename(os.path.normpath(a.out)), "seed": a.seed,
                "n": {k: len(v) for k, v in parts.items()}, "n_gold": len(gold),
                "families": {k: len({family_of(r) for r in v}) for k, v in parts.items()},
                "cells": {k: dict(Counter(r["cell"] for r in v)) for k, v in parts.items()},
                "sha256": {n: sha256(f"{a.out}/{n}") for n in ("train.jsonl", "calib.jsonl", "test.jsonl", "gold.csv")},
                "note": "gold.csv is a subset of test.jsonl meant to be edited by hand; run_eval logs the sha256 of the files it actually used."}
    json.dump(manifest, open(f"{a.out}/manifest.json", "w"), indent=1)
    print(json.dumps(manifest, indent=1))
