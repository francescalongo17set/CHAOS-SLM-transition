"""Stage 10: package post/*.jsonl into final/{train,validation,test_package}. Run: python -I code/package.py"""
import json, hashlib, re, shutil, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
F = ROOT/"final"
def jl(p): return [json.loads(l) for l in open(ROOT/p, encoding="utf-8")]
def clean(o):
    if isinstance(o, str): return re.sub("[  \u0085]", " ", o)
    if isinstance(o, list): return [clean(x) for x in o]
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items() if k not in ("kind", "job_id")}
    return o
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
R = [clean(r) for r in jl("post/router.jsonl")]; Q = [clean(q) for q in jl("post/qa.jsonl")]
state = json.load(open(ROOT/"plan/STATE.json")); rc = json.load(open(ROOT/"index/retrieval_config.json"))
ISO = re.compile(r"zurich_impresa|zurich impresa|allianz|periodical4life", re.I)
DIRS = {"train": "train", "validation": "validation", "test": "test_package"}
for d in DIRS.values():
    if (F/d).exists(): shutil.rmtree(F/d)
    (F/d).mkdir(parents=True)
summary = {}
for sp, d in DIRS.items():
    rs = [r for r in R if r["support"]["split"] == sp]; qs = [q for q in Q if q["support"]["split"] == sp]
    for name, rows in (("router.jsonl", rs), ("qa.jsonl", qs)):
        with open(F/d/name, "w", encoding="utf-8") as f:
            for x in rows: f.write(json.dumps(x, ensure_ascii=False) + "\n")
        back = [json.loads(l) for l in open(F/d/name, encoding="utf-8")]
        assert len(back) == len(rows)
    if sp != "test":  # isolation: nothing of the test-only material
        blob = open(F/d/"router.jsonl", encoding="utf-8").read() + open(F/d/"qa.jsonl", encoding="utf-8").read()
        hits = ISO.findall(blob)
        assert not hits, (sp, Counter(h.lower() for h in hits))
    man = {"split": sp, "release_status": "draft_unreviewed", "verified_share": 0.0, "seed": 20261110,
           "counts": {"router": len(rs), "qa": len(qs)},
           "router_route_balance": dict(Counter(r["support"]["expected_route"] for r in rs)),
           "router_feature_balance": dict(Counter(r["labels"]["feature"] for r in rs)),
           "qa_behavior_balance": dict(Counter(q["support"]["expected_behavior"] for q in qs)),
           "qa_type_balance": dict(Counter(q["support"]["question_type"] for q in qs)),
           "writer_models": dict(Counter(x["support"]["generator"] for x in rs + qs)),
           "validator_version": "validate.py 0.2", "writer_card": "writer_card.md (v3)", "retrieval_config": rc,
           "cap_levels": state.get("qa_cap_levels"),
           "files": {n: {"sha256": sha(F/d/n), "records": c} for n, c in (("router.jsonl", len(rs)), ("qa.jsonl", len(qs)))}}
    json.dump(man, open(F/d/"manifest.json", "w"), indent=1, ensure_ascii=False)
    summary[sp] = man["counts"]
assert sum(v["router"] for v in summary.values()) == len(R) and sum(v["qa"] for v in summary.values()) == len(Q)
(F/"code").mkdir(exist_ok=True)
for p in (ROOT/"code").glob("*.py"): shutil.copy(p, F/"code"/p.name)
shutil.copy(ROOT/"code/requirements.txt", F/"code/requirements.txt")
print(summary)
