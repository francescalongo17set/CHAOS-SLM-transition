"""Stage 8 post-process (book section 14, stage 8).

Run from data/:  python -I code/postprocess.py [--out post] [--no-retrieval] [--extra FOLDER ...]

Steps (all logged in <out>/report.json and <out>/dropped.jsonl):
 1  merge   every accepted folder in MERGE_ORDER (later wins by id), drop plan/superseded_qa.json
         'dropped_no_replacement', drop records of plan/dropped_jobs.json, hold the comparison router
         records of u_* folders (HOLD_*; owner decision pending), exclude h_003/h_004 (never merged).
 2  normalise generator ids (subagent-*-alias -> claude-<model>-5-5).
 3  retrieval for every QA record (server needed): evidence_record, retrieval_hit (any gold in top 5),
         gold_rank (best gold rank); retrieval_all_gold is kept for multi_fact. Answerable misses are dropped.
 4  hard negatives for records tagged hard_negative: top 5 must hold a non-gold chunk with a field of the
         gold chunk and another coverage; otherwise the lowest non-gold chunk is swapped (gold never removed).
 5  pairs: a router record whose pair partner was dropped is dropped.
 6  de-duplication (exact + edit-distance within a split, pair/bundle members excluded) and contamination
         filter (13-word n-gram and edit distance of train/validation against test).
 7  test isolation assertions (Impresa chunks / Allianz only in test) and count tables vs plan.
Outputs: <out>/router.jsonl, <out>/qa.jsonl, <out>/report.json, <out>/dropped.jsonl.
Nothing under final/ is written (that is stage 10).
"""
import argparse, glob, json, os, re, sys, random, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
SEED = 20261110
EDIT_RATIO = 0.92       # near-duplicate threshold within a split (normalised similarity); logged
CONTAM_RATIO = 0.90     # train/validation vs test
NGRAM = 13

FIXED_ORDER = ["pilot/stg", "staging/trial/final", "staging/bulk/final_b1", "staging/bulk/final_b2",
               "staging/bulk/final_b3", "staging/bulk/final_b4", "staging/bulk/u_repl3", "staging/bulk/final_b5"]
GLOB_ORDER = ["h_001", "h_002", "h_0[0-4][0-9]", "r_h_*", "r_s_*", "u_00*", "v_0*", "w_*", "x_*", "y_*", "z_*"]
NEVER = {"h_003", "h_004", "v_new"}
HOLD_FOLDER_PREFIX = "u_00"          # comparison router records of these folders are held back
HOLD_SCENARIOS = {"router_only_agentic_comparison", "router_only_lightweight_simple_comparison"}


def jl(path):
    p = ROOT / path
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def folders(extra):
    out = list(FIXED_ORDER)
    seen = set(out)
    for pat in GLOB_ORDER:
        for d in sorted(glob.glob(str(ROOT / "staging/bulk" / pat))):
            name = os.path.basename(d)
            rel = f"staging/bulk/{name}"
            if name in NEVER or rel in seen or not os.path.isdir(d):
                continue
            if name == "h_001" or name == "h_002" or re.fullmatch(r"h_0(0[5-9]|[1-4]\d)", name) or not name.startswith("h_"):
                out.append(rel); seen.add(rel)
    for e in extra:
        if e not in seen:
            out.append(e)
    return out


def norm_generator(g):
    if g and "alias" in g:
        return "claude-haiku-5-5" if "haiku" in g else "claude-sonnet-5-5"
    return g


def words(t):
    return re.findall(r"\w+", t.lower())


def ngrams(ws, n):
    return {" ".join(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="post")
    ap.add_argument("--no-retrieval", action="store_true", help="skip step 3 and 4 (no server)")
    ap.add_argument("--extra", nargs="*", default=[], help="more folders merged last (relative to data/)")
    ap.add_argument("--no-hold", action="store_true", help="do not hold u_* comparison router records")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(exist_ok=True)
    rep = {"folders": [], "steps": {}}
    dropped = []

    def drop(kind, rid, why, **kw):
        dropped.append({"kind": kind, "id": rid, "why": why, **kw})

    # plan lookups
    jobs = {}
    q2job, qa2job = {}, {}
    for l in open(ROOT / "plan/jobs.jsonl", encoding="utf-8"):
        j = json.loads(l)
        jobs[j["job_id"]] = j
        for r in j["records"]:
            if r["kind"] == "router":
                q2job[r["fixed"]["query_id"]] = j["job_id"]
            else:
                qa2job[r["fixed"]["qa_id"]] = j["job_id"]
    superseded = json.load(open(ROOT / "plan/superseded_qa.json"))
    drop_qa_ids = set(superseded["dropped_no_replacement"])
    dropped_jobs = set(json.load(open(ROOT / "plan/dropped_jobs.json"))["jobs"])

    # 1 merge
    router, qa = {}, {}
    src_r, src_q = {}, {}
    held = 0
    for f in folders(a.extra):
        nr = nq = 0
        for r in jl(f"{f}/accepted_router.jsonl"):
            qid = r["query_id"]
            job = q2job.get(qid)
            if (not a.no_hold) and os.path.basename(f).startswith(HOLD_FOLDER_PREFIX) and job and jobs[job]["scenario"] in HOLD_SCENARIOS:
                held += 1
                drop("router", qid, "held_comparison_pending_owner_decision", folder=f)
                continue
            router[qid] = r; src_r[qid] = f; nr += 1
        for r in jl(f"{f}/accepted_qa.jsonl"):
            qa[r["qa_id"]] = r; src_q[r["qa_id"]] = f; nq += 1
        rep["folders"].append({"folder": f, "router": nr, "qa": nq})
    for qid in list(qa):
        if qid in drop_qa_ids:
            del qa[qid]; drop("qa", qid, "superseded_dropped_no_replacement")
    for qid in list(router):
        if qid in superseded.get("dropped_router", {}):
            del router[qid]; drop("router", qid, "stage9_blind_pass_drop")
    for qid in list(router):
        if q2job.get(qid) in dropped_jobs:
            del router[qid]; drop("router", qid, "job_skipped_twice")
    for qid in list(qa):
        if qa2job.get(qid) in dropped_jobs:
            del qa[qid]; drop("qa", qid, "job_skipped_twice")
    for r in list(router.values()) + list(qa.values()):
        r["support"]["generator"] = norm_generator(r["support"].get("generator"))
    rep["steps"]["merge"] = {"router": len(router), "qa": len(qa), "held_comparison": held}

    # 3 retrieval
    chunks = {}
    for l in open(ROOT / "chunks/chunks.jsonl", encoding="utf-8"):
        c = json.loads(l); chunks[c["chunk_id"]] = c
    cat = {}
    for l in open(ROOT / "catalogue/chunk_catalogue.jsonl", encoding="utf-8"):
        c = json.loads(l); cat[c["chunk_id"]] = c
    if not a.no_retrieval:
        from retrieve import retrieve
        stats = collections.Counter()
        rng = random.Random(SEED)
        by_doc_pool = collections.defaultdict(list)
        for cid, c in cat.items():
            by_doc_pool[(c["doc_id"], c["pool"])].append(cid)
        for qid in sorted(qa):
            r = qa[qid]
            s = r["support"]
            doc = s["family"].split("__")[0]
            hits = retrieve(r["question"], doc, 5)
            gold = set(s["gold_chunk_ids"])
            ev = [{"rank": h["rank"], "chunk_id": h["chunk_id"], "section_path": h["section_path"], "page": h["page"], "text": h["text"]} for h in hits]
            if s["expected_behavior"] == "answer":
                ranks = [h["rank"] for h in hits if h["chunk_id"] in gold]
                s["retrieval_hit"] = bool(ranks)
                s["gold_rank"] = min(ranks) if ranks else None
                s["retrieval_all_gold"] = len(ranks) == len(gold)
                stats["answerable"] += 1
                if not ranks:
                    stats["miss"] += 1
                    drop("qa", qid, "retrieval_miss", job=qa2job.get(qid))
                    r["_drop"] = True
                    continue
                # 4 hard negatives
                if "hard_negative" in s.get("noise_tags", []):
                    stats["hn_planned"] += 1
                    gf = set().union(*[set(cat[g]["fields_found"]) for g in gold if g in cat]) if gold else set()
                    gcov = {cat[g]["coverage"] for g in gold if g in cat}

                    def is_hn(cid):
                        c = cat.get(cid)
                        return bool(c) and cid not in gold and bool(set(c["fields_found"]) & gf) and c["coverage"] not in gcov
                    if any(is_hn(e["chunk_id"]) for e in ev):
                        stats["hn_ok"] += 1
                    else:
                        pool = cat[next(iter(gold))]["pool"] if next(iter(gold)) in cat else None
                        cand = [cid for cid, c in cat.items() if c["doc_id"] == doc and c["pool"] == pool and is_hn(cid)
                                and cid not in {e["chunk_id"] for e in ev}]
                        victim = [i for i in range(len(ev) - 1, -1, -1) if ev[i]["chunk_id"] not in gold]
                        if cand and victim:
                            cid = rng.choice(sorted(cand))
                            c = chunks[cid]
                            ev[victim[0]] = {"rank": ev[victim[0]]["rank"], "chunk_id": cid, "section_path": c["section_path"],
                                             "page": c["page"], "text": c["text"], "hard_negative_swap": True}
                            stats["hn_swapped"] += 1
                            s["gold_rank"] = min(e["rank"] for e in ev if e["chunk_id"] in gold)
                        else:
                            stats["hn_unmet"] += 1
                            s["noise_tags"] = [t for t in s["noise_tags"] if t != "hard_negative"]
            else:
                s["retrieval_hit"] = None; s["gold_rank"] = None
            r["evidence_record"] = ev
        for qid in [q for q, r in qa.items() if r.get("_drop")]:
            del qa[qid]
        rep["steps"]["retrieval"] = dict(stats)
    else:
        rep["steps"]["retrieval"] = "skipped"

    # 5 pairs
    pair = collections.defaultdict(list)
    for qid, r in router.items():
        if r["support"].get("pair_id"):
            pair[r["support"]["pair_id"]].append(qid)
    np_ = 0
    for pid, ids in pair.items():
        if len(ids) < 2:
            for qid in ids:
                del router[qid]; drop("router", qid, "pair_partner_missing", pair_id=pid); np_ += 1
    rep["steps"]["pairs"] = {"pair_ids": len(pair), "dropped_orphans": np_}

    # 6 de-dup + contamination
    from rapidfuzz import fuzz
    def key(t): return " ".join(words(t))
    items = [("router", qid, r["query"], r["support"]["split"], r["support"].get("bundle_id"), r["support"].get("pair_id")) for qid, r in router.items()]
    items += [("qa", qid, r["question"], r["support"]["split"], r["support"].get("bundle_id"), None) for qid, r in qa.items()]
    removed = set()
    seen = {}
    for kind, rid, t, sp, b, p in sorted(items, key=lambda x: x[1]):
        k = (kind, key(t))
        if k in seen:
            removed.add((kind, rid)); drop(kind, rid, "exact_duplicate", of=seen[k])
        else:
            seen[k] = rid
    near = collections.Counter()
    for kind in ("router", "qa"):
        for sp in ("train", "validation", "test"):
            grp = [(rid, key(t), b, p) for k, rid, t, s, b, p in items if k == kind and s == sp and (kind, rid) not in removed]
            grp.sort(key=lambda x: len(x[1]))
            for i, (rid, t, b, p) in enumerate(grp):
                if (kind, rid) in removed:
                    continue
                for rid2, t2, b2, p2 in grp[i + 1:]:
                    if len(t2) > len(t) * 1.3 + 5:
                        break
                    if (kind, rid2) in removed or (b and b == b2) or (p and p == p2):
                        continue
                    if fuzz.ratio(t, t2) >= EDIT_RATIO * 100:
                        removed.add((kind, rid2)); near[kind] += 1
                        drop(kind, rid2, "near_duplicate", of=rid, ratio=round(fuzz.ratio(t, t2) / 100, 3))
    test = [(kind, rid, key(t)) for kind, rid, t, sp, b, p in items if sp == "test" and (kind, rid) not in removed]
    tng = {k: set() for k in ("router", "qa")}
    for kind, rid, t in test:
        tng[kind] |= ngrams(t.split(), NGRAM)
    contam = collections.Counter()
    for kind, rid, t, sp, b, p in items:
        if sp == "test" or (kind, rid) in removed:
            continue
        tk = t if False else key(t)
        hit = None
        if tng[kind] & ngrams(tk.split(), NGRAM):
            hit = "13gram"
        else:
            for k2, rid2, t2 in test:
                if k2 == kind and abs(len(t2) - len(tk)) <= 0.3 * len(tk) + 5 and fuzz.ratio(tk, t2) >= CONTAM_RATIO * 100:
                    hit = "edit_distance"; break
        if hit:
            removed.add((kind, rid)); contam[kind + ":" + hit] += 1
            drop(kind, rid, "contamination_" + hit, split=sp)
    for kind, rid in removed:
        (router if kind == "router" else qa).pop(rid, None)
    rep["steps"]["dedup"] = {"exact_or_near_removed": len(removed) - sum(contam.values()), "near_by_kind": dict(near),
                             "contamination": dict(contam), "edit_ratio": EDIT_RATIO, "contam_ratio": CONTAM_RATIO, "ngram": NGRAM}
    # pairs again (dedup may have removed a member)
    pair = collections.defaultdict(list)
    for qid, r in router.items():
        if r["support"].get("pair_id"):
            pair[r["support"]["pair_id"]].append(qid)
    for pid, ids in pair.items():
        if len(ids) < 2:
            for qid in ids:
                del router[qid]; drop("router", qid, "pair_partner_missing_after_dedup", pair_id=pid)

    # 7 test isolation + counts
    viol = []
    for kind, d in (("router", router), ("qa", qa)):
        for rid, r in d.items():
            sp = r["support"]["split"]
            if sp == "test":
                continue
            blob = json.dumps(r, ensure_ascii=False)
            if "zurich_impresa" in blob or "allianz" in blob.lower():
                viol.append((kind, rid, sp))
    for kind, rid, sp in viol:
        (router if kind == "router" else qa).pop(rid, None)
        drop(kind, rid, "test_isolation_violation", split=sp)
    rep["steps"]["isolation_violations_removed"] = len(viol)

    def cnt(d, kind):
        c = collections.Counter()
        for r in d.values():
            s = r["support"]
            c[s["split"]] += 1
        return dict(c)
    rep["final"] = {"router": len(router), "qa": len(qa), "router_by_split": cnt(router, "r"), "qa_by_split": cnt(qa, "q"),
                    "target": {"router": {"train": 2100, "validation": 300, "test": 600}, "qa": {"train": 850, "validation": 150, "test": 500}}}
    rt = collections.Counter(r["support"]["expected_route"] for r in router.values())
    rep["final"]["router_by_route"] = dict(rt)
    ab = collections.Counter(r["support"]["expected_behavior"] for r in qa.values())
    rep["final"]["qa_by_behavior"] = dict(ab)
    rep["dropped_by_reason"] = dict(collections.Counter(d["why"] for d in dropped))

    with open(out / "router.jsonl", "w", encoding="utf-8") as f:
        for qid in sorted(router):
            f.write(json.dumps(router[qid], ensure_ascii=False) + "\n")
    with open(out / "qa.jsonl", "w", encoding="utf-8") as f:
        for qid in sorted(qa):
            f.write(json.dumps(qa[qid], ensure_ascii=False) + "\n")
    with open(out / "dropped.jsonl", "w", encoding="utf-8") as f:
        for d in dropped:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    json.dump(rep, open(out / "report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: rep[k] for k in ("steps", "final", "dropped_by_reason")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
