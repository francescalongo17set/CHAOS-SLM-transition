"""After a Kaggle training run: register the new weights as `challenger`, and promote them to `champion` only if
they are better. Weights already registered (same hash) are skipped, so re-running is safe.

    python scripts/ci_register.py <downloaded kernel output folder>

Promotion rule: no drop in unsafe-query recall on test or gold, and a higher mean routing accuracy (test + gold).
"""
import os
import sys

SAFETY = ("test_safety_recall", "gold_safety_recall")
ACCURACY = ("test_acc_route", "gold_acc_route")


def better(new: dict, champ: dict) -> bool:
    """new / champ are MLflow metric dicts. Safety may not regress; routing accuracy must improve."""
    if any(new[k] < champ[k] for k in SAFETY):
        return False
    return sum(new[k] for k in ACCURACY) > sum(champ[k] for k in ACCURACY)


if __name__ == "__main__":
    from mlflow import MlflowClient

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from register_model import MODEL, model_version, register

    out = sys.argv[1]
    model_dir, metrics = f"{out}/laya_ft", f"{out}/runs/finetuned/metrics.json"
    c = MlflowClient()
    sha = model_version(model_dir)
    if any(v.tags.get("weights_sha") == sha for v in c.search_model_versions(f"name='{MODEL}'")):
        print(f"weights {sha} already registered: nothing to do")
        sys.exit(0)

    mv = register(model_dir, metrics, "challenger")
    new = c.get_run(mv.run_id).data.metrics
    try:
        champ_mv = c.get_model_version_by_alias(MODEL, "champion")
    except Exception:  # no champion yet
        champ_mv = None
    if champ_mv is None or better(new, c.get_run(champ_mv.run_id).data.metrics):
        c.set_registered_model_alias(MODEL, "champion", mv.version)
        print(f"version {mv.version} promoted to champion (was: {champ_mv.version if champ_mv else 'none'})")
    else:
        print(f"version {mv.version} stays challenger; champion is still version {champ_mv.version}")
