"""FT-P1 step 3 unit tests: checkpoint verification and run.json patching, no GPU, no `laya` import."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_ft_laya as R   # noqa: E402

TR = {"model": "convaiinnovations/laya/multilingual", "revision": "85cc74dd", "epoch_selected": 3, "temperature": [1.4, 1.1, 1.0],
      "temperature_by_options": {}, "temperature_clamped": {}, "n_by_bucket": {"choice:3-5": 189}, "items": {"calibration": 514},
      "config": {"epochs": 4}, "epochs": [{"epoch": 0}], "sanity": {"passed": True}}


def make_ck(tmp_path, cfg=None):
    run = tmp_path / "run"
    ck = run / "checkpoint"
    ck.mkdir(parents=True)
    (ck / "model.safetensors").write_bytes(b"weights")
    (ck / "rl_agent_config.json").write_text(json.dumps(cfg or {"fine_tuned": True, "temperature": [1.4, 1.1, 1.0]}))
    (run / "train_report.json").write_text(json.dumps(TR))
    return ck


def agent(ck, temps=(1.4, 1.1, 1.0), by=None, model_id=None):
    return SimpleNamespace(model_id=model_id or str(ck), temperature_raw=list(temps), temperature_by_options_raw=by or {})


def test_verify_accepts_the_requested_checkpoint(tmp_path):
    ck = make_ck(tmp_path)
    assert R.verify_loaded(agent(ck), ck)["fine_tuned"] is True


@pytest.mark.parametrize("kw,msg", [({"model_id": "convaiinnovations/laya"}, "requested"), ({"temps": (1, 1, 1)}, "temperatures"),
                                     ({"by": {"choice:2": 2.0}}, "per-bucket")])
def test_verify_stops_on_another_checkpoint(tmp_path, kw, msg):
    ck = make_ck(tmp_path)
    with pytest.raises(SystemExit, match=msg):
        R.verify_loaded(agent(ck, **kw), ck)


def test_verify_stops_on_a_base_checkpoint(tmp_path):
    ck = make_ck(tmp_path, {"temperature": [1.4, 1.1, 1.0]})
    with pytest.raises(SystemExit, match="fine_tuned"):
        R.verify_loaded(agent(ck), ck)


def test_patch_run_json_adds_fields_and_is_idempotent(tmp_path):
    ck = make_ck(tmp_path)
    rj = tmp_path / "run.json"
    rj.write_text(json.dumps({"model_size": {"params_total": 5}, "notes": "n", "model_id": "x", "model_revision": "y"}))
    out = R.patch_run_json(rj, ck, ck.parent / "train_report.json", "laya-ft-multilingual-a", "ds-name")
    sha = R.sha256(ck / "model.safetensors")
    assert out["weights_sha256"] == sha and out["kaggle_dataset"] == "ds-name" and out["epoch_selected"] == 3
    assert out["finetuned_from"] == {"model": TR["model"], "revision": "85cc74dd"}
    assert out["temperature_fit"]["temperature"] == [1.4, 1.1, 1.0] and out["temperature_fit"]["calibration_items"] == 514
    assert (out["model_id"], out["model_revision"]) == R.ft_identity(ck.parent / "train_report.json", sha, "laya-ft-multilingual-a")
    assert out["model_revision"] == "ft:" + sha[:16] and out["model_size"]["disk_mb"] == R.dir_mb(ck) and out["model_size"]["params_total"] == 5
    again = R.patch_run_json(rj, ck, ck.parent / "train_report.json", "laya-ft-multilingual-a", "ds-name")
    assert again == out and out["notes"].count("softmax(T * log p)") == 1
