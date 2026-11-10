import os
import gradio as gr, mlflow
from mlflow import MlflowClient
from orch.backends import LayaBackend
from orch.router import Orchestrator

os.environ["AWS_ACCESS_KEY_ID"] = os.environ["AWS_RO_ACCESS_KEY_ID"]          # the app only reads weights
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ["AWS_RO_SECRET_ACCESS_KEY"]

mlflow.set_experiment("orchestrator-app")
mv = MlflowClient().get_model_version_by_alias("laya-router", "champion")
cache = f"models_cache/{mv.version}"
path = os.path.join(cache, "laya")
if not os.path.exists(os.path.join(path, "model.safetensors")):
    path = mlflow.artifacts.download_artifacts(artifact_uri=mv.source, dst_path=cache)
orch = Orchestrator(LayaBackend(path))

@mlflow.trace(name="web_request")
def handle(query):
    mlflow.update_current_trace(tags={"registry_version": mv.version, "source": "gradio"})
    r = orch.run(query)
    return r.route, r.reason

gr.Interface(handle, gr.Textbox(label="Query"),
             [gr.Textbox(label="Route"), gr.Textbox(label="Reason")]).launch()