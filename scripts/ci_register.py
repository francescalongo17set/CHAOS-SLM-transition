"""After a Kaggle training run: register the new weights as `challenger`, and promote them to `champion` only if
they are better. Weights already registered (same hash) are skipped, so re-running is safe.

    python scripts/ci_register.py <downloaded kernel output folder>

Promotion rule: no drop in unsafe-query recall on test or gold, and a higher mean routing accuracy (test + gold).
Prints markdown (the pipeline appends it to the job summary), including the paths to open in the MLflow UI.
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

    def links(v):  # MLflow here has no public address: these paths go after your UI's, e.g. http://127.0.0.1:5001/
        exp = c.get_run(v.run_id).info.experiment_id
        return (f"- MLflow model version: `#/models/{MODEL}/versions/{v.version}`\n"
                f"- MLflow run (metrics, weights): `#/experiments/{exp}/runs/{v.run_id}`\n"
                f"- MLflow traces of the page: `#/experiments` > orchestrator-app (GenAI mode)")

    sha = model_version(model_dir)
    existing = [v for v in c.search_model_versions(f"name='{MODEL}'") if v.tags.get("weights_sha") == sha]
    if existing:
        print(f"### MLflow\nWeights `{sha}` are already registered as version {existing[0].version}: nothing to do.\n{links(existing[0])}")
        sys.exit(0)

    mv = register(model_dir, metrics, "challenger")
    new = c.get_run(mv.run_id).data.metrics
    try:
        champ_mv = c.get_model_version_by_alias(MODEL, "champion")
    except Exception:  # no champion yet
        champ_mv = None
    if champ_mv is None or better(new, c.get_run(champ_mv.run_id).data.metrics):
        c.set_registered_model_alias(MODEL, "champion", mv.version)
        verdict = f"Version {mv.version} promoted to **champion** (was: {champ_mv.version if champ_mv else 'none'})."
    else:
        verdict = f"Version {mv.version} stays **challenger**; champion is still version {champ_mv.version}."
    print(f"### MLflow\n{verdict}\n{links(mv)}")
