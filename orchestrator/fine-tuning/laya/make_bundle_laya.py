"""Build the Kaggle Dataset folder for the Laya fine-tuning notebook (pattern of kev/make_bundle_ft.py).

  python orchestrator/fine-tuning/laya/make_bundle_laya.py          # -> orchestrator/fine-tuning/dist/laya-ft-bundle/

Layout is the repo layout (baselines/common/data.py finds the data at <root>/data-generation/data/final_v2):
  orchestrator/baselines/{common,laya,audit,requirements-common.txt,pytest.ini}     (imported, never edited)
  orchestrator/fine-tuning/{common,laya,data/laya,data/manifest.json}
  data-generation/data/final_v2/{train,validation,test}/{router.jsonl,manifest.json}
Upload as a PRIVATE Kaggle Dataset. Run `python common/build_data.py` first so data/laya exists. No weights, no secrets.
"""
import shutil
import sys
from pathlib import Path

FT = Path(__file__).resolve().parents[1]                 # orchestrator/fine-tuning
BASE = FT.parent / "baselines"
REPO = FT.parents[1]
OUT = FT / "dist" / "laya-ft-bundle"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "*.ipynb_checkpoints")


def main():
    for need in (FT / "data" / "manifest.json", FT / "data" / "laya" / "train.jsonl",
                 FT / "data" / "laya" / "calibration.jsonl", FT / "data" / "laya" / "development.jsonl"):
        if not need.exists():
            sys.exit(f"missing {need}: run orchestrator/fine-tuning/common/build_data.py first")
    if OUT.exists():
        shutil.rmtree(OUT)
    ob, of = OUT / "orchestrator" / "baselines", OUT / "orchestrator" / "fine-tuning"
    for d in ("common", "laya", "audit"):
        shutil.copytree(BASE / d, ob / d, ignore=IGNORE)
    for f in ("requirements-common.txt", "pytest.ini"):
        shutil.copy2(BASE / f, ob / f)
    for d in ("common", "laya"):
        shutil.copytree(FT / d, of / d, ignore=IGNORE)
    shutil.copytree(FT / "data" / "laya", of / "data" / "laya")
    shutil.copy2(FT / "data" / "manifest.json", of / "data" / "manifest.json")
    for split in ("train", "validation", "test"):
        dst = OUT / "data-generation" / "data" / "final_v2" / split
        dst.mkdir(parents=True)
        for f in ("router.jsonl", "manifest.json"):
            shutil.copy2(REPO / "data-generation" / "data" / "final_v2" / split / f, dst / f)
    n = sum(1 for p in OUT.rglob("*") if p.is_file())
    mb = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file()) / 1e6
    print(f"{OUT}: {n} files, {mb:.1f} MB")


if __name__ == "__main__":
    main()
