"""Gradio front end. Serves whatever `laya-router@champion` points at, and switches by itself when the alias moves."""
import os
import shutil
import threading
import time

import gradio as gr
import mlflow
from mlflow import MlflowClient

from orch.backends import LayaBackend
from orch.router import Orchestrator

os.environ["AWS_ACCESS_KEY_ID"] = os.environ["AWS_RO_ACCESS_KEY_ID"]          # the app only reads weights
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ["AWS_RO_SECRET_ACCESS_KEY"]
CHECK_EVERY = 30  # seconds between registry lookups, done on the next request, so an idle app costs nothing

mlflow.set_experiment("orchestrator-app")
client = MlflowClient()
lock = threading.Lock()
served = {"version": None, "orch": None, "checked": 0.0}


def load_champion():
    mv = client.get_model_version_by_alias("laya-router", "champion")
    if mv.version == served["version"]:
        return
    cache = f"models_cache/{mv.version}"
    path = os.path.join(cache, "laya")
    if not os.path.exists(os.path.join(path, "model.safetensors")):
        path = mlflow.artifacts.download_artifacts(artifact_uri=mv.source, dst_path=cache)
    old = served["version"]
    served.update(version=mv.version, orch=Orchestrator(LayaBackend(path)))
    if old:
        shutil.rmtree(f"models_cache/{old}", ignore_errors=True)  # ~650 MB per version
    print(f"serving laya-router version {mv.version}", flush=True)


def current():
    with lock:
        if time.time() - served["checked"] > CHECK_EVERY:
            served["checked"] = time.time()
            try:
                load_champion()
            except Exception as e:  # registry or bucket briefly unreachable: keep serving the loaded model
                print("registry check failed, still serving version", served["version"], "-", e, flush=True)
        return served["version"], served["orch"]


load_champion()  # at startup a failure should stop the app, not hide


@mlflow.trace(name="web_request")
def handle(query):
    version, orch = current()
    mlflow.update_current_trace(tags={"registry_version": version, "source": "gradio"})
    r = orch.run(query)
    return r.route, r.reason


gr.Interface(handle, gr.Textbox(label="Query"),
             [gr.Textbox(label="Route"), gr.Textbox(label="Reason")]).launch()
