"""Build the Kaggle Dataset folder (no git clone needed on Kaggle). One bundle serves the Kev and Laya notebooks (v2 data).

  python kev/make_bundle.py            # -> orchestrator/baselines/dist/kev-bundle/

Layout is the repo layout, because common/data.py finds the data at <repo>/data-generation/data/final_v2:
  kev-bundle/orchestrator/baselines/{common,kev,laya,audit,requirements-common.txt,pytest.ini}
  kev-bundle/data-generation/data/final_v2/{train,validation,test}/{router.jsonl,manifest.json}
Upload the folder as a PRIVATE Kaggle Dataset (the data is synthetic but not ours to publish).
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # orchestrator/baselines/
REPO = ROOT.parents[1]                              # repo root
OUT = ROOT / "dist" / "kev-bundle"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "*.ipynb_checkpoints")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    ob = OUT / "orchestrator" / "baselines"
    for d in ("common", "kev", "laya", "audit"):
        shutil.copytree(ROOT / d, ob / d, ignore=IGNORE)
    for f in ("requirements-common.txt", "pytest.ini"):
        shutil.copy2(ROOT / f, ob / f)
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
