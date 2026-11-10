import random
import sys

sys.path.insert(0, "scripts")
import gen_queries as g  # noqa: E402  (torch is only imported under __main__, so this is CPU-safe)

INS = [{"source": "D.Lgs. 209/2005", "ref": f"art.{i}", "text": f"Testo {i}"} for i in range(5)]
OTHER = [{"source": "ITA-CaseHold", "ref": "x", "text": "Materia amministrativa"}]


def test_every_cell_builds_a_prompt_with_language_and_count():
    for cell, (_q, n, *_labels) in g.CELLS.items():
        for lang, name in (("it", "Italian"), ("en", "English")):
            text, refs = g.prompt(cell, n, lang, INS, OTHER, random.Random(1))
            assert name in text and str(n) in text and refs


def test_cell_quotas_total_300_per_scale_unit_and_labels_are_consistent():
    assert sum(c[0] for c in g.CELLS.values()) == 300  # x --scale 10 = 3,000
    for _q, _n, scope, cx, safety in g.CELLS.values():
        assert (cx == "n/a") == (scope == "out_of_scope" or safety == "unsafe")


def test_collect_drops_invalid_and_keeps_language():
    cache = {"light-r0-000": {"call_id": "light-r0-000", "cell": "light", "lang": "it", "refs": ["a"],
                              "raw": '{"queries": ["Quanto dura il termine per denunciare il sinistro?", "boh"]}'}}
    rows = g.collect(cache)["light"]
    assert len(rows) == 1 and rows[0]["language"] == "it"


def test_family_ids_differ_across_laws_and_casehold_judgments():
    assert g.fam({"source": "D.Lgs. 209/2005", "ref": "Art. 1", "text": "a"}) != g.fam({"source": "Codice civile", "ref": "Art. 1", "text": "a"})
    assert g.fam({"source": "ITA-CaseHold", "ref": "x", "text": "uno"}) != g.fam({"source": "ITA-CaseHold", "ref": "x", "text": "due"})
