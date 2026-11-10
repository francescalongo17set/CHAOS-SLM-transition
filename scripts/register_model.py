import json, shutil, sys, tempfile
import mlflow
from mlflow import MlflowClient
sys.path.insert(0, ".")
from orch.backends import model_version

model_dir, metrics_json = sys.argv[1:3]
res = json.load(open(metrics_json))
tmp = tempfile.mkdtemp() + "/laya"
shutil.copytree(model_dir, tmp, ignore=shutil.ignore_patterns("checkpoint_latest"))

mlflow.set_experiment("orchestrator-laya")
loc = mlflow.get_experiment_by_name("orchestrator-laya").artifact_location
assert loc.startswith("s3://"), f"weights would be stored locally ({loc}); recreate the experiment with the bucket location"
with mlflow.start_run(run_name=res["model"]) as run:
    mlflow.log_params({"model_version": res["model_version"], **{f"t_{k}": v for k, v in res["thresholds"].items()}})
    mlflow.log_metrics({f"{s}_{k}": v for s in ("test", "gold") for k, v in res[s].items() if k != "n" and v == v})
    mlflow.log_artifacts(tmp, "laya")

c = MlflowClient()
try:
    c.get_registered_model("laya-router")
except mlflow.exceptions.MlflowException:  # first registration in this database
    c.create_registered_model("laya-router")
# plain weights folder, not an MLflow model flavor: register_model("runs:/...") rejects it, so point at the artifact URI
mv = c.create_model_version("laya-router", source=f"{run.info.artifact_uri}/laya", run_id=run.info.run_id)
c.set_model_version_tag("laya-router", mv.version, "weights_sha", model_version(model_dir))
alias = sys.argv[3] if len(sys.argv) > 3 else "challenger"  # promote to "champion" by hand, or pass it as the 3rd argument
c.set_registered_model_alias("laya-router", alias, mv.version)
print("registered version", mv.version, "alias", alias)