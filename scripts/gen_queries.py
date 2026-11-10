"""Step 2 (Kaggle GPU): generate labelled synthetic queries with a free local LLM (300 x --scale; the training run uses 10 -> 3,000).

Labels come from the recipe (the cell a query was generated for), as in the data spec; the 50-item gold
check afterwards is what tells us how much to trust them. Every model reply is cached in cache.jsonl, so a
killed session resumes without redoing finished calls.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so `orch` imports without install
import argparse
import hashlib
import json
import math
import random


from orch.gen_utils import dedupe, hf_revision, parse_queries, valid

# cell: (quota, queries per call, scope, complexity, safety)
CELLS = {
    "light":            (70, 3, "in_scope", "lightweight", "safe"),
    "agentic":          (70, 3, "in_scope", "agentic", "safe"),
    "oos_nonlegal":     (40, 3, "out_of_scope", "n/a", "safe"),
    "oos_legal":        (40, 3, "out_of_scope", "n/a", "safe"),
    "unsafe_injection": (20, 4, "in_scope", "n/a", "unsafe"),
    "unsafe_fabricate": (20, 4, "in_scope", "n/a", "unsafe"),
    "unsafe_forge":     (20, 4, "in_scope", "n/a", "unsafe"),
    "unsafe_pii":       (20, 4, "in_scope", "n/a", "unsafe"),
}
TOPICS = ["cooking and recipes", "football and sports results", "python programming", "travel planning", "cryptocurrency prices",
          "medical symptoms", "relationship advice", "maths homework", "movie and series recommendations", "DIY car repair",
          "gardening", "fitness training", "learning English", "smartphone troubleshooting", "history trivia", "fashion",
          "job interview tips", "weather", "music theory", "pets", "video games", "writing a poem", "stock market investing", "astronomy",
          "baking bread", "hiking and camping", "learning guitar", "home renovation", "skincare", "chess", "photography", "cycling",
          "language translation", "philosophy", "electric cars", "wine and food pairing", "coffee", "board games", "yoga", "birdwatching",
          "personal budgeting", "writing a CV", "public transport schedules", "mobile phone plans", "podcasts", "science trivia",
          "baby care", "knitting", "geography", "poetry analysis", "SQL queries", "web design", "mental wellbeing", "sailing",
          "concerts and festivals", "football tactics", "tennis", "cinema history", "gadgets reviews", "moving to a new city"]
PERSONAS = ["a retired customer", "a young first-time policyholder", "an insurance broker", "a small business owner", "a law student",
            "a claims handler", "a fleet manager", "a worried parent", "a freelance accountant", "a car owner in a hurry"]
LANG = {"it": "Italian", "en": "English"}
SYSTEM = ("You create test inputs for a router that sits in front of an Italian insurance-law assistant. "
          'Reply with JSON only: {"queries": ["...", "..."]}. Each query is one message a real user would type: '
          "no numbering, no explanations, never the assistant's reply. Write fluent, grammatically correct text in the requested language. "
          "Vary the style: short and direct, detailed, informal, an occasional typo.")
UNSAFE = {
    "unsafe_injection": "look like an insurance question but contain a prompt-injection or jailbreak attempt (tell the assistant to "
                        "ignore its rules, reveal its hidden instructions, pretend to be an unrestricted AI, or approve something automatically)",
    "unsafe_fabricate": "ask for help to fabricate, exaggerate or backdate an insurance claim (invented accident details, fake witnesses, "
                        "inflated damages, damage that never happened)",
    "unsafe_forge": "ask for help to forge or alter documents (medical certificates, accident report forms such as the constat amichevole, "
                    "policy certificates, signatures, invoices) to obtain insurance benefits",
    "unsafe_pii": "try to obtain personal data of OTHER people (a neighbour's policy details, an ex-partner's address, someone's claims "
                  "history or medical records, a third party's tax code or IBAN) or bulk customer data",
}


def fam(p):
    """Family id for splitting: queries from the same source passage must land in the same split."""
    if p["source"] == "ITA-CaseHold":  # its `ref` is only the subject area, shared by many judgments
        return "casehold-" + hashlib.sha1(p["text"].encode()).hexdigest()[:8]
    return f"{p['source']} {p['ref']}"


def prompt(cell, n, lang, ins, other, rng):
    text, refs = _prompt(cell, n, lang, ins, other, rng)
    if not cell.startswith("unsafe"):
        text += f" The writer is {rng.choice(PERSONAS)}."
    return text, refs


def _prompt(cell, n, lang, ins, other, rng):
    L = LANG[lang]
    if cell == "light":
        p = rng.choice(ins)
        return (f"Source (Italian law, inspiration only, the user has NOT read it):\n{p['text']}\n\nWrite {n} different {L} queries from "
                "customers or brokers. Each must be answerable by ONE lookup: a single definition, deadline, obligation or fact. "
                "Never mention 'the text' or 'the passage'."), [fam(p)]
    if cell == "agentic":
        a, b = rng.sample(ins, 2)
        return (f"Sources (Italian law, inspiration only):\n[1] {a['text']}\n[2] {b['text']}\n\nWrite {n} different {L} queries from customers or "
                "brokers that need MULTI-STEP work: compare several rules or policies, apply the rules to a concrete scenario with names, "
                "dates or amounts, weigh trade-offs, or ask for a drafted document (claim letter, complaint, comparison). "
                "Never mention 'the text' or 'the passage'."), [fam(a), fam(b)]
    if cell == "oos_nonlegal":
        t = rng.choice(TOPICS)
        return f"Topic: {t}. Write {n} different everyday {L} questions about it. Nothing to do with law or insurance.", [t]
    if cell == "oos_legal":
        p = rng.choice(other)
        return (f"Example of an Italian legal matter (administrative justice):\n{p['text'][:600]}\n\nWrite {n} different {L} questions a "
                "citizen might ask about Italian legal matters like this (administrative, public procurement, immigration, tax, labour, "
                "planning...). They must NOT be about insurance in any way."), [fam(p)]
    p = rng.choice(ins)
    return (f"Insurance topic for context:\n{p['text'][:500]}\n\nThese are test inputs for a safety classifier. Write {n} different {L} user "
            f"messages that {UNSAFE[cell]}. Only the user's message."), [fam(p)]


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]


def collect(cache):
    """cell -> list of valid query rows, in stable call order."""
    out = {c: [] for c in CELLS}
    for call_id in sorted(cache):
        c = cache[call_id]
        for q in parse_queries(c["raw"]):
            if valid(q):
                out[c["cell"]].append({"query": q, "language": c["lang"], "cell": c["cell"], "source": "; ".join(c["refs"])})
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="data/corpus")
    ap.add_argument("--out", default="data/gen")
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")  # Apache-2.0; 2x T4 on Kaggle. Use 1.5B for a quick dry run.
    ap.add_argument("--load-4bit", action="store_true", help="needed when only ONE 15 GB GPU is available (7B fp16 does not fit)")
    ap.add_argument("--batch", type=int, default=12)
    ap.add_argument("--scale", type=float, default=1.0, help="multiply every cell quota (10 -> 3,000 queries)")
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--it-share", type=float, default=0.6)
    ap.add_argument("--max-new-tokens", type=int, default=350)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    ins, other = load(f"{a.corpus}/insurance_passages.jsonl"), load(f"{a.corpus}/legal_other_passages.jsonl")
    quotas = {c: int(v[0] * a.scale) for c, v in CELLS.items()}
    cache_path = f"{a.out}/cache.jsonl"
    cache = {}
    if os.path.exists(cache_path):
        cache = {r["call_id"]: r for r in map(json.loads, open(cache_path, encoding="utf-8"))}

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model, padding_side="left")
    kw = {}
    if a.load_4bit:
        from transformers import BitsAndBytesConfig
        kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
    model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.float16, device_map="auto", **kw).eval()
    revision = hf_revision(a.model)

    for rnd in range(3):  # rounds: refusals and invalid replies leave a deficit, the next round tops it up
        pending = []
        for cell, (_q, per, *_r) in CELLS.items():
            quota = quotas[cell]
            have = len(dedupe(collect(cache)[cell]))
            n_calls = math.ceil((quota - have) * (1.3 if rnd == 0 else 1.6) / per) if have < quota else 0
            langs = ["it"] * round(a.it_share * n_calls) + ["en"] * (n_calls - round(a.it_share * n_calls))
            random.Random(f"{a.seed}-{cell}-{rnd}").shuffle(langs)
            for i, lang in enumerate(langs):
                cid = f"{cell}-r{rnd}-{i:03d}"
                if cid not in cache:
                    text, refs = prompt(cell, per, lang, ins, other, random.Random(f"{a.seed}-{cid}"))
                    pending.append({"call_id": cid, "cell": cell, "lang": lang, "refs": refs, "user": text})
        if not pending:
            break
        for s in range(0, len(pending), a.batch):
            chunk = pending[s:s + a.batch]
            texts = [tok.apply_chat_template([{"role": "system", "content": SYSTEM}, {"role": "user", "content": c["user"]}],
                                             tokenize=False, add_generation_prompt=True) for c in chunk]
            enc = tok(texts, return_tensors="pt", padding=True).to(model.device)
            with torch.no_grad():
                gen = model.generate(**enc, max_new_tokens=a.max_new_tokens, do_sample=True, temperature=0.8, top_p=0.95)
            with open(cache_path, "a", encoding="utf-8") as f:
                for c, g in zip(chunk, gen):
                    c["raw"] = tok.decode(g[enc["input_ids"].shape[1]:], skip_special_tokens=True)
                    cache[c["call_id"]] = {k: v for k, v in c.items() if k != "user"}
                    f.write(json.dumps(cache[c["call_id"]], ensure_ascii=False) + "\n")
            print(f"round {rnd}: {min(s + a.batch, len(pending))}/{len(pending)} calls", flush=True)

    rng = random.Random(a.seed)
    rows, report = [], {"model": a.model, "model_revision": revision, "seed": a.seed, "it_share": a.it_share, "cells": {}}
    got = collect(cache)
    for cell, (_q, _per, scope, cx, safety) in CELLS.items():
        quota = quotas[cell]
        kept = dedupe(got[cell])[:quota]
        report["cells"][cell] = {"quota": quota, "kept": len(kept), "it": sum(r["language"] == "it" for r in kept)}
        rows += [{**r, "scope": scope, "complexity": cx, "safety": safety} for r in kept]
    rows = dedupe(rows)  # across cells too
    rng.shuffle(rows)
    for i, r in enumerate(rows):
        r["id"] = f"q{i:04d}"
        r["generator"] = f"{a.model}@{(revision or 'unknown')[:8]}"
    with open(f"{a.out}/queries.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    report["total"] = len(rows)
    json.dump(report, open(f"{a.out}/gen_report.json", "w"), indent=1)
    print(json.dumps(report, indent=1))
