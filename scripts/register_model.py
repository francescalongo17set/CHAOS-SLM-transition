"""Upload fine-tuned Laya weights + eval metrics to MLflow and register them as a new `laya-router` version.

    python scripts/register_model.py <laya_ft folder> <metrics.json> [alias]     # alias defaults to "challenger"

Needs MLFLOW_TRACKING_URI (Postgres) and the bucket credentials (AWS_*, MLFLOW_S3_ENDPOINT_URL) in the environment.
"""
import json
import os
import shutil
import sys
import tempfile

import mlflow
from mlflow import MlflowClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so `orch` imports without install
from orch.backends import model_version

EXPERIMENT, MODEL = "orchestrator-laya", "laya-router"


def register(model_dir, metrics_json, alias="challenger"):
    res = json.load(open(metrics_json))
    tmp = tempfile.mkdtemp() + "/laya"
    shutil.copytree(model_dir, tmp, ignore=shutil.ignore_patterns("checkpoint_latest"))  # training checkpoint: not needed, 660 MB

    mlflow.set_experiment(EXPERIMENT)
    loc = mlflow.get_experiment_by_name(EXPERIMENT).artifact_location
    assert loc.startswith("s3://"), f"weights would be stored locally ({loc}); recreate the experiment with the bucket location"
    with mlflow.start_run(run_name=res["model"]) as run:
        mlflow.log_params({"model_version": res["model_version"], **{f"t_{k}": v for k, v in res["thresholds"].items()}})
        mlflow.log_metrics({f"{s}_{k}": v for s in ("test", "gold") for k, v in res[s].items() if k != "n" and v == v})
        mlflow.log_artifacts(tmp, "laya")

    c = MlflowClient()
    try:
        c.get_registered_model(MODEL)
    except mlflow.exceptions.MlflowException:  # first registration in this database
        c.create_registered_model(MODEL)
    # plain weights folder, not an MLflow model flavor: register_model("runs:/...") rejects it, so point at the artifact URI
    mv = c.create_model_version(MODEL, source=f"{run.info.artifact_uri}/laya", run_id=run.info.run_id)
    c.set_model_version_tag(MODEL, mv.version, "weights_sha", model_version(model_dir))
    c.set_registered_model_alias(MODEL, alias, mv.version)
    return mv


if __name__ == "__main__":
    mv = register(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "challenger")
    print("registered version", mv.version)
