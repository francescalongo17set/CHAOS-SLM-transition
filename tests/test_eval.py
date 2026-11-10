import pytest

from orch.decision import Decision
from orch.evalkit import gold_route, knee, load_rows, metrics, sweep, tune_stops
from orch.gen_utils import dedupe, norm, parse_queries, valid
from orch.router import Thresholds


def row(i, scope="in_scope", cx="lightweight", safety="safe"):
    return {"id": i, "scope": scope, "complexity": cx, "safety": safety}


def dec(unsafe=0.0, out=0.0, light=1.0):
    return {"safety": Decision.from_probs({"safe": 1 - unsafe, "unsafe": unsafe}),
            "scope": Decision.from_probs({"in_scope": 1 - out, "out_of_scope": out}),
            "complexity": Decision.from_probs({"lightweight": light, "agentic": 1 - light})}


ROWS = [row("easy"), row("hard", cx="agentic"), row("oos", "out_of_scope", "n/a"), row("bad", "in_scope", "n/a", "unsafe")]


def test_gold_route():
    assert [gold_route(r) for r in ROWS] == ["lightweight", "agentic", "stop", "stop"]


def test_perfect_model_scores_perfectly():
    d = {"easy": dec(light=0.95), "hard": dec(light=0.1), "oos": dec(out=0.9), "bad": dec(unsafe=0.9)}
    m = metrics(ROWS, d, Thresholds())
    assert m["acc_route"] == 1 and m["false_escalation"] == 0 and m["false_lightweight"] == 0 and m["safety_recall"] == 1
    assert m["cost"] == pytest.approx((1 + 5 + 0 + 0) / 4)


def test_error_rates_are_counted_on_the_right_denominator():
    d = {"easy": dec(light=0.5), "hard": dec(light=0.99), "oos": dec(), "bad": dec()}  # every decision wrong
    m = metrics(ROWS, d, Thresholds())
    assert m["false_escalation"] == 1 and m["false_lightweight"] == 1
    assert m["safety_recall"] == 0 and m["stop_recall"] == 0 and m["acc_route"] == 0


def test_sweep_cost_grows_with_threshold_and_knee_is_found():
    d = {"easy": dec(light=0.9), "hard": dec(light=0.3), "oos": dec(out=0.9), "bad": dec(unsafe=0.9)}
    pts = sweep(ROWS, d, Thresholds(), [0.5, 0.8, 0.95])
    assert [p["cost"] for p in pts] == sorted(p["cost"] for p in pts)
    assert pts[knee(pts)]["t_lightweight"] == 0.5  # 0.5 already gets everything right at the lowest cost


def test_knee_picks_the_bend():
    pts = [{"cost": c, "acc_route": a} for c, a in [(1, 0.5), (2, 0.9), (3, 0.92), (5, 0.93)]]
    assert knee(pts) == 1


def test_load_rows_rejects_label_typos(tmp_path):
    p = tmp_path / "g.csv"
    p.write_text("id,query,scope,complexity,safety\n1,q,in_scope,lightwieght,safe\n", encoding="utf-8-sig")
    with pytest.raises(ValueError, match="complexity"):
        load_rows(p)
    p.write_text("id,query,scope,complexity,safety\n1,q,in_scope, agentic ,safe\n", encoding="utf-8-sig")
    assert load_rows(p)[0]["complexity"] == "agentic"  # stray spaces from hand editing are fine


def test_parse_queries_handles_messy_replies():
    assert parse_queries('Sure!\n```json\n{"queries": ["a b c d", "e f g h"]}\n```') == ["a b c d", "e f g h"]
    assert parse_queries('["uno due tre quattro"]') == ["uno due tre quattro"]
    assert parse_queries("no json here") == []
    assert parse_queries('{"queries": [1, "ok"]}') == ["ok"]


def test_valid_and_dedupe():
    assert valid("Quanto costa la franchigia RC auto?") and not valid("troppo corta") and not valid("In the passage above, what is X?")
    assert norm("È così!") == "e cosi"
    assert len(dedupe([{"query": "Che cos'è la polizza?"}, {"query": "che cosè la polizza"}])) == 1


def test_knee_ignores_points_that_cost_more_and_score_less():
    # accuracy falls as cost rises after index 1: the answer must be on the frontier, not the middle of the falling part
    pts = [{"cost": c, "acc_route": a} for c, a in [(1.1, 0.60), (1.3, 0.61), (1.7, 0.59), (2.2, 0.54), (2.9, 0.48)]]
    assert knee(pts) in (0, 1)  # the two frontier points; never 2, 3 or 4


def test_tune_stops_meets_recall_target_then_maximises_accuracy():
    rows = [row("ok1"), row("ok2"), row("bad1", "in_scope", "n/a", "unsafe"), row("bad2", "in_scope", "n/a", "unsafe")]
    d = {"ok1": dec(unsafe=0.25, light=0.9), "ok2": dec(unsafe=0.05, light=0.9),
         "bad1": dec(unsafe=0.9), "bad2": dec(unsafe=0.15)}
    th = tune_stops(rows, d, Thresholds(), target_recall=1.0)
    m = metrics(rows, d, th)
    assert m["safety_recall"] == 1.0 and th.unsafe <= 0.15  # must catch bad2; ok1 (0.25) then gets blocked
    th_lax = tune_stops(rows, d, Thresholds(), target_recall=0.5)
    assert metrics(rows, d, th_lax)["acc_route"] >= m["acc_route"]
