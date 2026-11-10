"""Build the Kaggle bundle in dist/: a code dataset, and three notebooks with their kernel-metadata.json.

    KAGGLE_USER=<your kaggle username> python scripts/make_kaggle.py
then follow README.md ("Run on Kaggle"). The notebooks only call the scripts in this repo.
  01-data     corpus + ~3,000 synthetic queries (Qwen 7B writes them) + train/calib/test/gold split
  02-smoke    5-minute proof that Laya's training and loading work (run this before the real one)
  03-train    full fine-tune of Laya-multilingual + evaluation + an untrained-Laya reference run
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER = os.environ.get("KAGGLE_USER", "YOUR_KAGGLE_USERNAME")
DIST = f"{ROOT}/dist"

SETUP = ["import glob, os, shutil, subprocess\n",
         "os.environ['USE_TF'] = '0'  # laya's model card: set this if laya.load() hangs\n",
         "# Kaggle mounts datasets under /kaggle/input/... (the exact path differs between Kaggle versions), so search for it.\n",
         "hits = glob.glob('/kaggle/input/**/orch/decision.py', recursive=True)\n",
         "assert hits, 'code dataset not attached:\\n' + subprocess.run('find /kaggle/input -maxdepth 4 | head -40', shell=True, capture_output=True, text=True).stdout\n",
         "src = os.path.dirname(os.path.dirname(hits[0]))\n",
         "# /kaggle/input is read-only; copy the code next to the outputs so scripts can write data/ and runs/\n",
         "shutil.copytree(src, '/kaggle/working/code', dirs_exist_ok=True)\n",
         "os.chdir('/kaggle/working/code')\n",
         "print('code from', src)\n"]

FIND = ["def find(name):\n",
        "    return glob.glob(f'/kaggle/input/**/{name}', recursive=True)[0]\n",
        "train, calib, test, gold = (find(n) for n in ('train.jsonl', 'calib.jsonl', 'test.jsonl', 'gold.csv'))\n",
        "print(train, calib, test, gold, sep='\\n')"]

PIP_LAYA = ["# laya = the decision model (Apache-2.0, PyPI). Installed on Kaggle only.\n",
            "!pip -q install laya mlflow matplotlib"]

NOTEBOOKS = {
    "01-data": ("Orchestrator 01 data", ["orchestrator-code"], True, [
        ["!pip -q install -U transformers accelerate bitsandbytes"],
        SETUP,
        ["# 1) sources -> passages + proof that D.Lgs. 209/2005 etc. are in the datasets (~2 min, downloads ~1 GB)\n",
         "!python scripts/build_corpus.py --out data/corpus"],
        ["# 2) ~3,000 queries with Qwen2.5-7B-Instruct (about 1.5-2.5 h; resumable: re-run the cell, it reads data/gen/cache.jsonl).\n",
         "# Two T4s: fp16. One GPU: 4-bit so it fits.\n",
         "import torch\n", "flag = '' if torch.cuda.device_count() >= 2 else '--load-4bit'\n", "print('gpus:', torch.cuda.device_count(), flag)\n",
         "!python scripts/gen_queries.py --corpus data/corpus --out data/gen --scale 10 --seed 14 --model Qwen/Qwen2.5-7B-Instruct {flag}"],
        ["# 3) split by source passage: train / calib / test, plus the 50-item gold CSV (taken from test)\n",
         "!python scripts/split.py --queries data/gen/queries.jsonl --out data/v2"],
        ["import pandas as pd\n", "pd.read_csv('data/v2/gold.csv').head(15)"],
        ["# copy the results to the Output tab so you can download them\n",
         "!mkdir -p /kaggle/working/out && cp -r data/v2 data/corpus/corpus_check.json data/gen/gen_report.json data/gen/queries.jsonl /kaggle/working/out/"],
    ]),
    "02-smoke": ("Orchestrator 02 smoke", ["orchestrator-code", "orchestrator-data-v2"], True, [
        PIP_LAYA,
        SETUP,
        FIND,
        ["# a few minutes: 120 queries, 1 epoch. Proves the data format, training and laya.load() all work.\n",
         "!python scripts/train_laya.py --train {train} --eval {calib} --out /kaggle/working/laya_smoke --smoke"],
        ["# scores calib/test/gold with the smoke model (numbers are meaningless; this checks the evaluation path)\n",
         "!python scripts/run_eval.py --model /kaggle/working/laya_smoke --calib {calib} --test {test} --gold {gold} "
         "--out /kaggle/working/runs/smoke --no-mlflow"],
    ]),
    "03-train": ("Orchestrator 03 train", ["orchestrator-code", "orchestrator-data-v2"], True, [
        PIP_LAYA,
        SETUP,
        FIND,
        ["# full fine-tune: 4 epochs on train.jsonl. laya saves checkpoint_latest/ after every epoch.\n",
         "!python scripts/train_laya.py --train {train} --eval {calib} --out /kaggle/working/laya_ft"],
        ["# evaluate: thresholds are tuned on calib only; test and gold are only reported.\n",
         "!python scripts/run_eval.py --model /kaggle/working/laya_ft --calib {calib} --test {test} --gold {gold} "
         "--out /kaggle/working/runs/finetuned --mlflow-uri sqlite:////kaggle/working/mlflow.db"],
        ["# reference: the same evaluation with the UNTRAINED Laya, to show how much the fine-tune adds\n",
         "!python scripts/run_eval.py --model convaiinnovations/laya-multilingual --calib {calib} --test {test} --gold {gold} "
         "--out /kaggle/working/runs/untrained --mlflow-uri sqlite:////kaggle/working/mlflow.db"],
        ["from IPython.display import Image\n", "Image('/kaggle/working/runs/finetuned/cost_vs_accuracy.png')"],
    ]),
}


def nb(cells):
    def cell(src):
        return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": src}
    return {"cells": [cell(c) for c in cells], "nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}}}


if __name__ == "__main__":
    shutil.rmtree(DIST, ignore_errors=True)
    code = f"{DIST}/code"
    os.makedirs(code)
    for d in ("orch", "scripts"):
        shutil.copytree(f"{ROOT}/{d}", f"{code}/{d}", ignore=shutil.ignore_patterns("__pycache__"))
    json.dump({"title": "orchestrator-code", "id": f"{USER}/orchestrator-code", "licenses": [{"name": "CC0-1.0"}]},
              open(f"{code}/dataset-metadata.json", "w"), indent=1)
    for slug, (title, datasets, gpu, cells) in NOTEBOOKS.items():
        d = f"{DIST}/{slug}"
        os.makedirs(d)
        json.dump(nb(cells), open(f"{d}/notebook.ipynb", "w"), indent=1)
        json.dump({"id": f"{USER}/orchestrator-{slug}", "title": title, "code_file": "notebook.ipynb", "language": "python",
                   "kernel_type": "notebook", "is_private": True, "enable_gpu": gpu, "enable_internet": True,
                   "dataset_sources": [f"{USER}/{x}" for x in datasets]}, open(f"{d}/kernel-metadata.json", "w"), indent=1)
    print(f"built {DIST} for Kaggle user {USER}", file=sys.stderr)
