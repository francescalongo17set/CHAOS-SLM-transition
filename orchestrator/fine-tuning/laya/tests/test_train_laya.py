"""FT-P1 unit tests: no GPU, no `laya` import (stand-ins)."""
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import train_laya as T   # noqa: E402

SCOPE = {"type": "choice", "criteria": {"in_scope": "a", "out_of_scope": "b", "quick_reply": "c"}}
FEAT = {"type": "choice", "criteria": {"product_policy_analysis": "a", "client_drafting": "b", "none": "c"}}
CPLX = {"type": "choice", "criteria": {"simple": "a", "complex": "b"}}


def row(scope, feat, cplx=None):
    qs = {"scope_check": SCOPE, "feature_classification": FEAT}
    exp = {"scope_check": scope, "feature_classification": feat}
    if cplx:
        qs["complexity_estimation"], exp["complexity_estimation"] = CPLX, cplx
    return {"state": "s", "questions": qs, "expected": exp}


ROWS = [row("in_scope", "product_policy_analysis", "simple"), row("in_scope", "product_policy_analysis", "complex"),
        row("out_of_scope", "none"), row("quick_reply", "none"), row("in_scope", "client_drafting", "simple")]


def test_skipped_items_stop_the_run():
    T.check_skipped({}, "train")
    with pytest.raises(T.Blocked, match="options_collapsed"):
        T.check_skipped({"options_collapsed": 1}, "train")


def test_dev_rows_get_all_three_questions_and_gold_routes():
    rows, gold = T.dev_route_rows(ROWS)
    assert all(list(r["questions"]) == list(T.QIDS) for r in rows)
    assert gold == ["lightweight", "agentic", "refuse", "quick_reply", "agentic"]
    assert rows[2]["expected"]["complexity_estimation"] == "simple"      # placeholder, unused
    assert ROWS[2]["questions"].keys() == {"scope_check", "feature_classification"}   # input not modified


def test_conflicting_question_definition_stops():
    bad = row("in_scope", "none", "simple")
    bad["questions"]["complexity_estimation"] = {**CPLX, "instructions": "other"}
    with pytest.raises(T.Blocked, match="defined differently"):
        T.dev_route_rows(ROWS + [bad])
    with pytest.raises(T.Blocked, match="never define"):
        T.dev_route_rows([row("out_of_scope", "none")])


def fake(rows, wrong=()):
    """items + records where the model prefers the gold label (or option 0 for rows in `wrong`)."""
    items, recs = [], []
    for i, r in enumerate(rows):
        for qid in T.QIDS:
            crit = (SCOPE, FEAT, CPLX)[T.QIDS.index(qid)]["criteria"]
            keys = list(crit)
            gold = keys.index(r["expected"][qid])
            pick = 0 if i in wrong else gold
            logits = [5.0 if c == pick else 0.0 for c in range(len(keys))]
            items.append({"q": {"crit": dict(crit)}})
            recs.append((0, logits, [], len(keys)))
    return items, recs


def test_predicted_routes_follow_argmax_and_dispatcher():
    rows, gold = T.dev_route_rows(ROWS)
    items, recs = fake(rows)
    assert T.predict_routes(recs, items, len(rows)) == gold
    items, recs = fake(rows, wrong={2})     # row 2: option 0 everywhere = in_scope, product_policy_analysis, simple
    assert T.predict_routes(recs, items, len(rows))[2] == "lightweight"
    assert T.route_scores(gold, T.predict_routes(recs, items, len(rows)))["route_accuracy"] == pytest.approx(0.8)


def test_length_mismatch_stops():
    rows, _ = T.dev_route_rows(ROWS)
    items, recs = fake(rows)
    with pytest.raises(T.Blocked, match="items"):
        T.predict_routes(recs[:-1], items[:-1], len(rows))


def test_epoch_selection_picks_best_development_value():
    h = [{"epoch": 0, "route_macro_f1": 0.9}, {"epoch": 1, "route_macro_f1": 0.5},
         {"epoch": 2, "route_macro_f1": 0.7}, {"epoch": 3, "route_macro_f1": 0.7}, {"epoch": 4, "route_macro_f1": 0.6}]
    assert T.select_epoch(h)["epoch"] == 2          # epoch 0 is the untrained start, ties go to the earlier epoch
    with pytest.raises(T.Blocked):
        T.select_epoch(h[:1])


def test_collapse_stops_the_run():
    T.check_collapse(None)
    with pytest.raises(T.Blocked, match="collapsed"):
        T.check_collapse("laya.train: predictions collapsed to the class prior (x)")


def test_sanity_floor_is_strict():
    assert T.sanity_check(0.396)["passed"] and not T.sanity_check(0.395)["passed"]
    assert T.SANITY_ROUTE_F1 == 0.395


def test_raw_probabilities_from_calibrated():
    logits, t = [2.0, 0.5, -1.0], 2.0
    z = [v / t for v in logits]
    cal = [math.exp(v) / sum(math.exp(w) for w in z) for v in z]
    raw = T.raw_from_calibrated(cal, t)
    want = [math.exp(v) / sum(math.exp(w) for w in logits) for v in logits]
    assert raw == pytest.approx(want, abs=1e-9)
    rounded = [round(p, 4) for p in cal]            # predict() rounds to 4 decimals
    assert max(T.raw_from_calibrated(rounded, t)) == pytest.approx(max(want), abs=2e-3)


def test_final_config_drops_base_bucket_temperatures():
    base = {"temperature": [1.0] * 3, "temperature_by_options": {"choice:2": 3.0}, "encoder": "e"}
    fitted = {"temperature": [1.5, 1.0, 1.0], "temperature_by_options": {}}
    out = T.final_config(base, 1024, 256, fitted)
    assert out["temperature"] == [1.5, 1.0, 1.0] and "temperature_by_options" not in out
    assert out["fine_tuned"] and out["max_len"] == 1024 and out["head_max_len"] == 256 and base["temperature_by_options"]


def test_epoch_callback_restores_training_mode_and_logs(tmp_path):
    class M:
        training = False
        def train(self):
            self.training = True
    m, saved, hist, log = M(), [], [], tmp_path / "epochs.jsonl"
    ticks = iter(range(0, 1000, 10))
    cb = T.make_epoch_callback(m, lambda: {"route_macro_f1": 0.6, "route_accuracy": 0.7, "n": 5}, saved.append, hist, log,
                               clock=lambda: next(ticks))
    cb(0, 1.25)
    assert m.training is True, "scoring leaves laya's model in eval mode; training mode must be restored"
    assert saved == [1] and hist[0]["epoch"] == 1 and hist[0]["mean_loss"] == 1.25
    assert json.loads(log.read_text())["route_macro_f1"] == 0.6


def test_read_rows_limit(tmp_path):
    p = tmp_path / "t.jsonl"
    p.write_text("".join(json.dumps({"i": i}) + "\n" for i in range(5)))
    assert len(T.read_rows(p)) == 5 and len(T.read_rows(p, 2)) == 2
