"""Build the Kaggle Dataset folder for the Kev fine-tuning notebook (pattern of baselines/kev/make_bundle.py, no git clone on Kaggle).

  python orchestrator/fine-tuning/kev/make_bundle_ft.py          # -> orchestrator/fine-tuning/dist/kev-ft-bundle/

Layout is the repo layout (common/data.py finds the data at <root>/data-generation/data/final_v2):
  orchestrator/baselines/{common,kev,audit,requirements-common.txt,pytest.ini}     (imported, never edited)
  orchestrator/fine-tuning/{common,kev,data/kev,data/manifest.json}
  data-generation/data/final_v2/{train,validation,test}/{router.jsonl,manifest.json}
Upload as a PRIVATE Kaggle Dataset. Run `python common/build_data.py` first so data/kev exists. No weights, no secrets.
"""
import shutil
import sys
from pathlib import Path

FT = Path(__file__).resolve().parents[1]                 # orchestrator/fine-tuning
BASE = FT.parent / "baselines"
REPO = FT.parents[1]
OUT = FT / "dist" / "kev-ft-bundle"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "*.ipynb_checkpoints")


def main():
    for need in (FT / "data" / "manifest.json", FT / "data" / "kev" / "train.jsonl"):
        if not need.exists():
            sys.exit(f"missing {need}: run orchestrator/fine-tuning/common/build_data.py first")
    if OUT.exists():
        shutil.rmtree(OUT)
    ob, of = OUT / "orchestrator" / "baselines", OUT / "orchestrator" / "fine-tuning"
    for d in ("common", "kev", "audit"):
        shutil.copytree(BASE / d, ob / d, ignore=IGNORE)
    for f in ("requirements-common.txt", "pytest.ini"):
        shutil.copy2(BASE / f, ob / f)
    for d in ("common", "kev"):
        shutil.copytree(FT / d, of / d, ignore=IGNORE)
    shutil.copytree(FT / "data" / "kev", of / "data" / "kev")
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
