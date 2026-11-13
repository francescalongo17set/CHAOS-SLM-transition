"""FT-P2 unit tests, no GPU and no upstream kev needed."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import train_kev as T   # noqa: E402

META = {"base": "Qwen/Qwen3.5-0.8B-Base", "base_revision": "abc123", "lora": 16, "head_dim": 256, "option_isolation": True,
        "special_embeddings": False, "weights_dtype": "fp32", "weights": "lora", "temperature": 2.351,
        "extra_args": {"lr": 2e-4, "lora_targets": "all", "batch": 1, "accum": 8, "checkpointing": 1}}
CFG = T.SIZES["0.8b"]


def flag(cmd, name):
    return cmd[cmd.index(name) + 1]


def test_architecture_comes_from_meta():
    cmd, s = T.build_command(META, CFG, "d/train.jsonl", "o/checkpoint")
    assert flag(cmd, "--base") == META["base"] and flag(cmd, "--base_revision") == "abc123"
    assert flag(cmd, "--lora") == "16" and flag(cmd, "--head_dim") == "256" and flag(cmd, "--lora_targets") == "all"
    assert flag(cmd, "--option_isolation") == "1" and flag(cmd, "--special_embeddings") == "0"
    assert flag(cmd, "--init_from") == CFG["init_from"] and "@9a45d25e" in CFG["init_from"]
    assert flag(cmd, "--dtype") == "fp32" and flag(cmd, "--weights_dtype") == "fp32"


def test_lr_is_capped_and_defaults_are_explicit():
    cmd, s = T.build_command(META, CFG, "d", "o")
    assert float(flag(cmd, "--lr")) == 5e-5 and s["meta_lr"] == 2e-4
    low = {**META, "extra_args": {**META["extra_args"], "lr": 3e-5}}
    assert float(flag(T.build_command(low, CFG, "d", "o")[0], "--lr")) == 3e-5
    for k, v in (("--epochs", "1"), ("--batch", "1"), ("--accum", "8"), ("--p_none_pair", "0.25"), ("--seed", "0"), ("--checkpointing", "1")):
        assert flag(cmd, k) == v
    assert "--replay" not in cmd and "--label_smoothing" not in cmd and "--focal_gamma" not in cmd and "--brier_w" not in cmd


def test_max_steps_only_when_asked():
    assert "--max_steps" not in T.build_command(META, CFG, "d", "o")[0]
    assert flag(T.build_command(META, CFG, "d", "o", max_steps=1)[0], "--max_steps") == "1"


def test_mismatch_and_missing_keys_stop():
    with pytest.raises(ValueError, match="weights_dtype"):
        T.build_command({**META, "weights_dtype": "bf16"}, CFG, "d", "o")
    with pytest.raises(ValueError, match="LoRA only"):
        T.build_command({**META, "weights": "full"}, CFG, "d", "o")
    with pytest.raises(ValueError, match="lora_targets"):
        T.build_command({**META, "extra_args": {"lr": 1e-5}}, CFG, "d", "o")


def test_difference_from_released_is_reported():
    _, s = T.build_command({**META, "extra_args": {**META["extra_args"], "accum": 4}}, CFG, "d", "o")
    assert s["differs_from_released"] == {"accum": [4, 8]}


def test_limit_file(tmp_path):
    src = tmp_path / "t.jsonl"
    src.write_text("".join(json.dumps({"i": i}) + "\n" for i in range(10)))
    dst = tmp_path / "s.jsonl"
    assert T.limit_file(src, 3, dst) == 3 and len(dst.read_text().splitlines()) == 3


def test_run_json_patch(tmp_path):
    import run_ft
    ck = tmp_path / "checkpoint"; ck.mkdir()
    (ck / "adapter_model.safetensors").write_bytes(b"a"); (ck / "head.pt").write_bytes(b"h")
    (tmp_path / "train_report.json").write_text(json.dumps({"init_from": "x@y", "released_meta": {"base": "b", "base_revision": "r"},
                                                          "released": {"resolved": "/p", "weights_sha256": "w"}, "command": ["c"],
                                                          "training_metrics": {"peak_device_bytes": 5}}))
    (tmp_path / "calibration").mkdir(); (tmp_path / "calibration" / "temperature.json").write_text(json.dumps({"value": 1.7}))
    rj = tmp_path / "run.json"
    rj.write_text(json.dumps({"model_size": {"disk_mb_base": 100.0}, "notes": "n"}))
    out = run_ft.patch_run_json(rj, ck, tmp_path / "train_report.json", tmp_path / "calibration" / "temperature.json", "0.8b", "kev-0.8b-ft-a")
    assert out["adapter_sha256"] == run_ft.sha256(ck / "adapter_model.safetensors") and out["head_sha256"]
    assert out["finetuned_from"]["base_revision"] == "r" and out["temperature_fit"]["value"] == 1.7 and out["train_run_id"] == "kev-0.8b-ft-a"
    assert out["model_size"]["disk_mb"] == round(out["model_size"]["disk_mb_adapter"] + 100.0, 1)
    assert json.loads(rj.read_text()) == out
