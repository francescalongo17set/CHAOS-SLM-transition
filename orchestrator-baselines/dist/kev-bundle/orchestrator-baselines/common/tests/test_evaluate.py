import json
import math
import pytest

from common import evaluate, report
from common.tests.helpers import make_log

SPLITS = ["validation", "test"]


def _dump(p, recs):
    with open(p, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


@pytest.mark.parametrize("split", SPLITS)
def test_perfect_log_gives_100(tmp_path, split):
    p = tmp_path / "p.jsonl"
    _dump(p, make_log(split, perfect=True))
    M = evaluate.evaluate(p, split, out_dir=tmp_path)
    for k in ("scope_check", "feature_classification", "complexity_estimation", "needs_clarification", "route"):
        assert M[k]["accuracy"] == 1.0, k
        assert M[k]["macro_f1"] == 1.0, k
        for c, v in M[k]["per_class"].items():
            if v["support"]:
                assert v["precision"] == v["recall"] == v["f1"] == 1.0, (k, c)
    assert M["needs_clarification"]["positive_class"]["f1"] == 1.0
    assert M["refuse_recall"]["all"]["recall"] == 1.0
    assert M["refuse_recall"]["safety_leak"]["recall"] == 1.0
    for k, v in M["calibration"].items():
        if k.startswith("slots"):
            assert v["ece"] < 0.05  # oracle's C-29 workaround mislabels a few slots on purpose
        else:
            assert v["ece"] == 0.0 and v["brier"] == 0.0, k
    assert M["route_attribution"] == {}
    assert M["dispatcher_oracle"]["matches"] == M["dispatcher_oracle"]["n"]
    assert (tmp_path / f"metrics_{split}.json").exists()
    assert "Report" in report.render(M)


def test_random_log_near_chance_and_stable(tmp_path):
    p = tmp_path / "r.jsonl"
    _dump(p, make_log("test", perfect=False, seed=1))
    M1 = evaluate.evaluate(p, "test")
    M2 = evaluate.evaluate(p, "test")
    assert json.dumps(M1, sort_keys=True) == json.dumps(M2, sort_keys=True)
    assert M1["scope_check"]["accuracy"] < 0.7  # chance is ~1/3
    assert M1["feature_classification"]["accuracy"] < 0.45
    assert 0.0 < M1["calibration"]["scope_check"]["brier"] < 1.5
    wrong = round(M1["route"]["n"] * (1 - M1["route"]["accuracy"]))
    assert sum(M1["route_attribution"].values()) == wrong
    report.render(M1)


def test_error_rows_count_as_wrong(tmp_path):
    recs = make_log("validation", perfect=True)
    for r in recs[:10]:
        r["error"], r["answers"] = "boom", None
    p = tmp_path / "e.jsonl"
    _dump(p, recs)
    M = evaluate.evaluate(p, "validation")
    assert M["n_error_rows"] == 10
    assert M["scope_check"]["accuracy"] < 1.0
    assert M["route_attribution"].get("call error") == 10


def test_rejects_invalid_log(tmp_path):
    recs = make_log("validation")[:-1]
    p = tmp_path / "bad.jsonl"
    _dump(p, recs)
    with pytest.raises(ValueError):
        evaluate.evaluate(p, "validation")


def test_prf_and_ece_hand_checked():
    m = evaluate.prf(["a", "a", "b", "b"], ["a", "b", "b", "b"], ["a", "b"])
    assert m["accuracy"] == 0.75
    assert m["per_class"]["a"]["precision"] == 1.0 and m["per_class"]["a"]["recall"] == 0.5
    assert math.isclose(m["macro_f1"], (2 / 3 + 0.8) / 2)
    # confident and always wrong: ECE 1, Brier 2
    r = evaluate.ece_brier([({"x": 1.0, "y": 0.0}, "y")] * 4, ["x", "y"])
    assert r["ece"] == 1.0 and r["brier"] == 2.0
