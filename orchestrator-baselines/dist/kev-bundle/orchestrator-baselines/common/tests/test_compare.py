import json
from common import compare, evaluate
from common.tests.helpers import make_log


def _metrics(tmp_path, pipeline, device, mode):
    p = tmp_path / f"{pipeline}.jsonl"
    with open(p, "w") as f:
        for r in make_log("validation"):
            r["pipeline"] = pipeline
            f.write(json.dumps(r) + "\n")
    M = evaluate.evaluate(p, "validation")
    M["run"] = {"device": device, "latency_mode": mode}
    return M


def test_zero_one_three(tmp_path):
    assert "No runs available" in compare.build({})
    assert "no run provided yet" in compare.build({"kev-0.8b": _metrics(tmp_path, "kev", "T4", "in_process")})
    runs = {"kev-0.8b": _metrics(tmp_path, "kev", "T4", "in_process"),
            "laya": _metrics(tmp_path, "laya", "P100", "in_process"),
            "nimble": _metrics(tmp_path, "nimble", None, "http_hosted")}
    out = compare.build(runs)
    assert "DIFFERENT" in out and "not comparable" in out and "None." in out


def test_dropped_reason():
    out = compare.build({}, {"nimble": "does not fit the free-tier GPU"})
    assert "dropped, does not fit" in out
