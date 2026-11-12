"""Stage 9 diversity check over post/*.jsonl. Writes post/diversity.json and post/diversity.md."""
import json, re, statistics as st, sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def jl(p): return [json.loads(l) for l in open(ROOT/p, encoding="utf-8")]
def fw(t):
    w = re.findall(r"\w+", t.lower()); return w[0] if w else ""
def stats(texts):
    n = len(texts); c = Counter(fw(t) for t in texts)
    top, k = c.most_common(1)[0]
    lens = [len(re.findall(r"\w+", t)) for t in texts]
    norm = [" ".join(re.findall(r"\w+", t.lower())) for t in texts]
    return {"n": n, "top_first_word": top, "top_share": round(k/n, 3),
            "dup_rate": round(1-len(set(norm))/n, 3),
            "len_mean": round(st.mean(lens), 1), "len_min": min(lens), "len_max": max(lens),
            "first3_distinct": round(len({" ".join(x.split()[:3]) for x in norm})/n, 3)}
R, Q = jl("post/router.jsonl"), jl("post/qa.jsonl")
cells = defaultdict(list)
for r in R: cells[("router", r["labels"]["feature"], r["support"]["expected_route"])].append(r["query"])
for q in Q: cells[("qa", q["support"]["question_type"], q["support"]["expected_behavior"])].append(q["question"])
out = []
for k, v in sorted(cells.items()):
    if len(v) < 20: continue
    s = stats(v); s["cell"] = "/".join(k); s["flag"] = s["top_share"] > 0.05 and s["n"] >= 20
    out.append(s)
json.dump(out, open(ROOT/"post/diversity.json", "w"), indent=1, ensure_ascii=False)
allr = stats([r["query"] for r in R]); allq = stats([q["question"] for q in Q])
md = ["# Diversity check", "", f"All router: {allr}", "", f"All QA: {allq}", "",
      "| cell | n | top first word | share | dup | mean words | min-max | flag (>5%) |", "|---|---|---|---|---|---|---|---|"]
for s in out:
    md.append(f"| {s['cell']} | {s['n']} | {s['top_first_word']} | {s['top_share']} | {s['dup_rate']} | {s['len_mean']} | {s['len_min']}-{s['len_max']} | {'YES' if s['flag'] else ''} |")
open(ROOT/"post/diversity.md", "w").write("\n".join(md))
print("\n".join(md))
