"""Stage 9: build review queues (CSV) from post/*.jsonl into review/. Nothing is marked verified."""
import json, csv, random
from pathlib import Path
random.seed(20261110)
ROOT = Path(__file__).resolve().parent.parent
def jl(p): return [json.loads(l) for l in open(ROOT/p, encoding="utf-8")]
R, Q = jl("post/router.jsonl"), jl("post/qa.jsonl")
(ROOT/"review").mkdir(exist_ok=True)
SENS = {"client_drafting", "ibip_screening"}
def rrow(r):
    s, l, c = r["support"], r["labels"], r["context"]
    flags = [t for t in s.get("noise_tags", []) if t in ("hard_negative",)]
    if s.get("safety_leak"): flags.append("safety_leak")
    return {"id": r["query_id"], "dataset": "router", "split": s["split"], "model_sees": json.dumps({"query": r["query"], "context": c}, ensure_ascii=False),
            "labels": json.dumps({"labels": l, "route": s["expected_route"], "slot_status": s["slot_status"]}, ensure_ascii=False),
            "flags": ";".join(flags), "decision": "", "comment": ""}
def qrow(q):
    s = q["support"]
    flags = []
    if s["expected_behavior"] == "absent": flags.append("absent")
    if not s.get("retrieval_hit", True): flags.append("retrieval_miss")
    return {"id": q["qa_id"], "dataset": "qa", "split": s["split"],
            "model_sees": json.dumps({"question": q["question"], "evidence": [e["text"][:600] for e in q["evidence_record"]]}, ensure_ascii=False),
            "labels": json.dumps({"behavior": s["expected_behavior"], "risposta": q["target"]["risposta"], "fonte": q["target"]["fonte"], "gold": s["gold_chunk_ids"]}, ensure_ascii=False),
            "flags": ";".join(flags), "decision": "", "comment": ""}
def write(name, rows):
    with open(ROOT/f"review/{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","dataset","split","model_sees","labels","flags","decision","comment"]); w.writeheader(); w.writerows(rows)
    print(name, len(rows))
write("test_router", [rrow(r) for r in R if r["support"]["split"] == "test"])
write("test_qa", [qrow(q) for q in Q if q["support"]["split"] == "test"])
write("leaked_unsafe_train_val", [rrow(r) for r in R if r["support"].get("safety_leak") and r["support"]["split"] != "test"])
write("absent_qa_all", [qrow(q) for q in Q if q["support"]["expected_behavior"] == "absent"])
rest = [r for r in R if r["support"]["split"] != "test" and not r["support"].get("safety_leak")]
samp = [r for r in rest if r["labels"]["feature"] in SENS or "hard_negative" in r["support"].get("noise_tags", [])]
others = [r for r in rest if r not in samp]
samp += random.sample(others, max(0, int(0.2*len(rest)) - len(samp)))
qrest = [q for q in Q if q["support"]["split"] != "test" and q["support"]["expected_behavior"] == "answer"]
qs = [q for q in qrest if not q["support"].get("retrieval_all_gold", True)] 
qs += random.sample([q for q in qrest if q not in qs], max(0, int(0.2*len(qrest)) - len(qs)))
write("sample_train_val", [rrow(r) for r in samp] + [qrow(q) for q in qs])
