"""Chapter 07 tests 1-6 (no GPU). A failing test is never edited to pass: it goes to the owner."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.append(str(HERE))
sys.path.append(str(HERE.parents[2]))

import build_data, checks, split                                          # noqa: E402
from orchestrator.baselines.common import data, dispatcher                 # noqa: E402
from orchestrator.baselines.common.questions import QuestionConfig        # noqa: E402
from orchestrator.baselines.common.state import serialize_state           # noqa: E402

QC = QuestionConfig()
ROWS = data.load_split("train")
EXS = build_data.build_examples(ROWS, QC)
BY = {r.query_id: r for r in ROWS}


def test_question_parity():                       # 1: built questions == what the eval adapter sends
    for ex in EXS:
        row = BY[ex.query_id]
        feature = row.labels["feature"]
        ref = {q.qid: q for q in QC.questions_for(feature)}      # evaluation builder, gold feature
        for q in ex.questions:
            assert q == ref[q.qid], (ex.query_id, q.qid)
        assert [q.qid for q in ex.questions] == [k for k in ref if k in ex.labels]


def date_only(row):
    """True if the only non-present slot is date_reference (never asked, C-29): gold route is a suspected label error (FT-C-24)."""
    bad = {k for k, v in row.support["slot_status"].items() if v != "present"}
    return bad == {"date_reference"}


def test_dispatcher_on_training_labels():         # 2: built labels -> dispatcher -> expected_route
    mismatched = []
    for ex in EXS:
        row = BY[ex.query_id]
        status = [ex.labels[q.qid] for q in ex.questions if q.qid.startswith("slot:")]
        need = any(v != "present" for v in status)                # from the BUILT labels only
        got = dispatcher.dispatch(ex.labels["scope_check"], ex.labels["feature_classification"],
                                  ex.labels.get("complexity_estimation"), need)
        if got != row.support["expected_route"]:
            mismatched.append(ex.query_id)
    # every mismatch is a date_reference-only row, and every such row mismatches (FT-C-24); nothing else may differ
    assert sorted(mismatched) == sorted(r.query_id for r in ROWS if date_only(r)), len(mismatched)
    assert len(mismatched) == 14


def test_rule_table():                            # 3
    n_insurer_skipped = 0
    for ex in EXS:
        row = BY[ex.query_id]
        ids = [q.qid for q in ex.questions]
        if row.labels["scope_check"] != "in_scope":
            assert "complexity_estimation" not in ids
        else:
            assert "complexity_estimation" in ids
        assert "slot:date_reference" not in ids
        for slot in QC.slots_for_feature(row.labels["feature"]):
            if slot not in row.support["slot_status"]:
                assert f"slot:{slot}" not in ids
                n_insurer_skipped += slot == "insurer"
        if row.labels["feature"] == "none":
            assert not any(i.startswith("slot:") for i in ids)
    assert n_insurer_skipped == 100


def test_split_on_real_data():                    # 4
    train_ids, calib_ids = split.calibration_split(ROWS, seed=build_data.SEED)
    parts = {"train": [BY[i] for i in train_ids], "calibration": [BY[i] for i in calib_ids],
             "development": data.load_split("validation")}
    checks.check_partitions(parts, {r.query_id for r in data.load_split("test")})
    assert len(train_ids) + len(calib_ids) == 2092


def test_split_is_deterministic():
    a = split.calibration_split(ROWS, seed=build_data.SEED)
    assert a == split.calibration_split(ROWS, seed=build_data.SEED)


def test_leaky_split_fails():                     # 4: a split that breaks a bundle must be rejected
    train_ids, calib_ids = split.calibration_split(ROWS, seed=build_data.SEED)
    bundle = next(r.support["bundle_id"] for r in ROWS if r.query_id in set(calib_ids)
                  and sum(x.support["bundle_id"] == r.support["bundle_id"] for x in ROWS) > 1)
    moved = next(r for r in ROWS if r.support["bundle_id"] == bundle and r.query_id in set(calib_ids))
    parts = {"train": [BY[i] for i in train_ids] + [moved], "calibration": [BY[i] for i in calib_ids if i != moved.query_id],
             "development": []}
    with pytest.raises(AssertionError):
        checks.check_partitions(parts, set())
    parts = {"train": [BY[i] for i in train_ids], "calibration": [BY[i] for i in calib_ids] + [BY[train_ids[0]]], "development": []}
    with pytest.raises(AssertionError):
        checks.check_partitions(parts, set())


def test_label_validity():                        # 5
    for ex in EXS:
        kev, laya = build_data.to_kev_record(ex), build_data.to_laya_record(ex)
        for qid, q in kev["questions"].items():
            assert q["label"] in q["criteria"]
        for qid, lab in laya["expected"].items():
            assert lab in laya["questions"][qid]["criteria"]
        assert list(kev["questions"]) == list(laya["questions"]) == list(laya["expected"])


def test_state_format():                          # 6
    for ex in EXS[:300]:
        row = BY[ex.query_id]
        s = serialize_state(row.model_input)
        assert ex.state == s and isinstance(build_data.to_kev_record(ex)["state"], str)
        assert build_data.to_kev_record(ex)["state"] == build_data.to_laya_record(ex)["state"] == s


def test_manifest_prefix(tmp_path):                # a one-format bundle must verify without the other format's files
    import json, shutil
    data_dir = HERE.parent / "data"
    for rel in json.loads((data_dir / "manifest.json").read_text())["files"]:
        if rel.startswith("kev/"):
            (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(data_dir / rel, tmp_path / rel)
    shutil.copy2(data_dir / "manifest.json", tmp_path / "manifest.json")
    checks.check_manifest(tmp_path, prefix="kev/")
    with pytest.raises(FileNotFoundError):
        checks.check_manifest(tmp_path)            # no prefix: the missing laya files are noticed
    with pytest.raises(AssertionError):
        checks.check_manifest(tmp_path, prefix="nope/")
