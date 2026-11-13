import json
import pytest

from common import data, logs, tokens
from common.questions import QuestionConfig
from common.state import serialize_state
from common.tests.helpers import make_log


def _dump(path, recs):
    with open(path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


@pytest.fixture(scope="module")
def good():
    return make_log("validation")


def test_perfect_log_validates(tmp_path, good):
    _dump(tmp_path / "v.jsonl", good)
    assert logs.validate_log(tmp_path / "v.jsonl", "validation") == []


def mutate(tmp_path, good, fn, drop=None):
    recs = json.loads(json.dumps(good))
    if drop is not None:
        recs = recs[:drop] + recs[drop + 1:]
    else:
        fn(recs)
    p = tmp_path / "m.jsonl"
    _dump(p, recs)
    return logs.validate_log(p, "validation")


def test_rejects_gap(tmp_path, good):
    assert any("missing from log" in e for e in mutate(tmp_path, good, None, drop=3))


def test_rejects_duplicate(tmp_path, good):
    assert any("duplicate" in e for e in mutate(tmp_path, good, lambda r: r.append(dict(r[0]))))


def test_rejects_bad_prob_sum(tmp_path, good):
    def f(r):
        p = r[0]["answers"]["scope_check"]["probs"]
        p["in_scope"], p["out_of_scope"], p["quick_reply"] = 0.5, 0.2, 0.2
    assert any("probs sum" in e for e in mutate(tmp_path, good, f))


def test_rejects_missing_option(tmp_path, good):
    def f(r):
        r[0]["answers"]["complexity_estimation"]["probs"].pop("complex")
    assert any("probs keys" in e for e in mutate(tmp_path, good, f))


def test_rejects_missing_latency(tmp_path, good):
    assert any("latency_ms" in e for e in mutate(tmp_path, good, lambda r: r[0].__setitem__("latency_ms", None)))


def test_rejects_reordered_options(tmp_path, good):
    def f(r):
        r[0]["answers"]["scope_check"]["option_order"] = ["out_of_scope", "in_scope", "quick_reply"]
    assert any("option_order" in e for e in mutate(tmp_path, good, f))


def test_rejects_wrong_slots_for_predicted_feature(tmp_path, good):
    def f(r):
        for x in r:
            if x["answers"]["slots"]:
                x["answers"]["slots"].pop(next(iter(x["answers"]["slots"])))
                break
    assert any("predicted-feature slots" in e for e in mutate(tmp_path, good, f))


def test_error_row_is_accepted_but_row_present(tmp_path, good):
    def f(r):
        r[0]["error"] = "oom"
        r[0]["answers"] = None
    assert mutate(tmp_path, good, f) == []


def test_writer_resume_after_torn_line(tmp_path, good):
    p = tmp_path / "r.jsonl"
    with logs.LogWriter(p) as w:
        for r in good[:5]:
            w.write(r)
    with open(p, "a") as f:
        f.write('{"query_id": "torn", "ans')  # killed mid-write
    w2 = logs.LogWriter(p)
    assert w2.is_done(good[0]["query_id"]) and not w2.is_done(good[5]["query_id"])
    with pytest.raises(ValueError):
        w2.write(good[0])
    for r in good[5:]:
        if not w2.is_done(r["query_id"]):
            w2.write(r)
    w2.close()
    # torn fragment stays in the file and is reported, not silently accepted
    errs = logs.validate_log(p, "validation")
    assert any("unparseable" in e for e in errs)


def test_writer_flushes_each_line(tmp_path, good):
    p = tmp_path / "f.jsonl"
    w = logs.LogWriter(p)
    w.write(good[0])
    assert len(p.read_text().splitlines()) == 1  # visible before close
    w.close()


@pytest.fixture(scope="module")
def tok():
    return tokens.RefTokenizer()


def test_ref_tokenizer_stable(tok):
    r = data.load_split("validation")[0]
    s = serialize_state(r.model_input)
    qs = QuestionConfig().questions_for("comparison")
    a, b = tok.count_ref(s, qs), tok.count_ref(s, qs)
    assert a == b > tok.count_state(s) > 0
