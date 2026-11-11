"""Stage 5c: deterministic planner (guideline book section 16).

Reads chunks, catalogue, absent candidates, comparable fields, seeds, client profiles.
Writes plan/jobs.jsonl, plan/STATE.json, plan/compatibility_matrix.csv, plan/plan_assertions.md.
Every choice is seeded (20261110) and iteration order is deterministic, so a restart gives the same ids.
"""
import csv, json, math, random, collections, itertools, re
from pathlib import Path
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "plan"
PLAN.mkdir(exist_ok=True)
SEED = 20261110
rng = random.Random(SEED)
SPL = ["train", "validation", "test"]
SPLIT_N = {"train": 2100, "validation": 300, "test": 600}
GENERATOR = json.load(open(ROOT / "logs/env.json"))["writer_model_id"]
LOG = ["Interpretation: the 20% section-spread cap (80 for Impresa) counts questions that have a source section, i.e. the answerable ones; absent questions have no gold chunk and are not counted."]


def note(msg):
    LOG.append(msg)
    print("NOTE:", msg)


# ----------------------------------------------------------------------------- helpers
def lr(total, weights):
    s = sum(weights)
    raw = [total * w / s for w in weights]
    fl = [int(math.floor(x)) for x in raw]
    for i in sorted(range(len(weights)), key=lambda i: (-(raw[i] - fl[i]), i))[: total - sum(fl)]:
        fl[i] += 1
    return fl


def round_matrix(rows, cols, allowed=None, target=None, lb=None, ub=None):
    """Integer matrix with exact row and column sums, closest (L1) to the proportional target."""
    R, C = len(rows), len(cols)
    N = sum(rows)
    assert N == sum(cols), (rows, cols)
    e = np.array(target, float) if target is not None else np.outer(rows, cols) / max(N, 1)
    nv = R * C
    A, lo, hi = [], [], []
    for i in range(R):
        r = np.zeros(2 * nv); r[i * C:(i + 1) * C] = 1; A.append(r); lo.append(rows[i]); hi.append(rows[i])
    for j in range(C):
        r = np.zeros(2 * nv); r[j:nv:C] = 1; A.append(r); lo.append(cols[j]); hi.append(cols[j])
    for k in range(nv):
        r = np.zeros(2 * nv); r[nv + k] = 1; r[k] = -1; A.append(r); lo.append(-e.flat[k]); hi.append(np.inf)
        r = np.zeros(2 * nv); r[nv + k] = 1; r[k] = 1; A.append(r); lo.append(e.flat[k]); hi.append(np.inf)
    xl = np.zeros(nv)
    xu = np.full(nv, float(N))
    if allowed is not None:
        xu = np.where(np.array(allowed).reshape(-1) > 0, xu, 0.0)
    if lb is not None:
        xl = np.array(lb, float).reshape(-1)
    if ub is not None:
        xu = np.minimum(xu, np.array(ub, float).reshape(-1))
    res = milp(np.concatenate([np.zeros(nv), np.ones(nv)]), constraints=LinearConstraint(np.array(A), lo, hi),
               integrality=np.concatenate([np.ones(nv), np.zeros(nv)]),
               bounds=Bounds(np.concatenate([xl, np.zeros(nv)]), np.concatenate([xu, np.full(nv, np.inf)])))
    assert res.success, f"round_matrix infeasible {rows} {cols}"
    return np.rint(res.x[:nv]).astype(int).reshape(R, C)


def pick(lst, n):
    """Seeded sample without replacement; fails loudly when the pool is short."""
    assert len(lst) >= n, f"pool too small: {len(lst)} < {n}"
    return rng.sample(lst, n)


# ----------------------------------------------------------------------------- data
CHUNKS = {}
for l in open(ROOT / "chunks/chunks.jsonl", encoding="utf-8"):
    c = json.loads(l); CHUNKS[c["chunk_id"]] = c
CAT = {}
for l in open(ROOT / "catalogue/chunk_catalogue.jsonl", encoding="utf-8"):
    c = json.loads(l); CAT[c["chunk_id"]] = c
ABSENT = [r for r in csv.DictReader(open(ROOT / "catalogue/absent_candidates.csv", encoding="utf-8")) if r["usable"] == "true"]
COMP = list(csv.DictReader(open(ROOT / "catalogue/comparable_fields.csv", encoding="utf-8")))
SEEDS = [json.loads(l) for l in open(ROOT / "seeds/seeds.jsonl", encoding="utf-8")]
PROFILES = [json.loads(l) for l in open(ROOT / "seeds/client_profiles.jsonl", encoding="utf-8")]
INSURER = {"zurich_salute": ("Zurich", "Salute"), "generali_immagina_adesso": ("Generali", "Immagina Adesso"), "zurich_impresa": ("Zurich", "Impresa")}
POOL_OF = {"train": "train_pool", "validation": "validation_pool", "test": "test_pool"}
DOCS2 = {"train": ["zurich_salute", "generali_immagina_adesso"], "validation": ["zurich_salute", "generali_immagina_adesso"], "test": ["zurich_impresa"]}
IBIP_DOC = {"train": "italiana_ri_plus", "validation": "italiana_ri_plus", "test": "allianz_periodical4life"}
CORE = {"train": ["zurich_salute", "generali_immagina_adesso", "italiana_ri_plus"], "validation": ["zurich_salute", "generali_immagina_adesso", "italiana_ri_plus"],
        "test": ["zurich_impresa", "allianz_periodical4life"]}


def fam_doc(doc, split):
    """Family of a chunk-based request: the product. Salute/Generali feed train and validation, so validation gets a suffix."""
    return doc + "__heldout" if split == "validation" else doc


# ----------------------------------------------------------------------------- quotas (book sections 5, 6, 9)
PA, CMP, REG, CD, IB = "product_policy_analysis", "comparison", "regulatory_consultation", "client_drafting", "ibip_screening"
GRID = {
    (PA, "simple"): {"lightweight": 560, "clarification": 65}, (PA, "complex"): {"clarification": 35, "agentic": 60},
    (CMP, "simple"): {"lightweight": 60, "clarification": 12}, (CMP, "complex"): {"clarification": 70, "agentic": 258},
    (REG, "simple"): {"lightweight": 310, "clarification": 18}, (REG, "complex"): {"clarification": 16, "agentic": 46},
    (CD, "simple"): {"clarification": 28, "agentic": 46}, (CD, "complex"): {"clarification": 114, "agentic": 182},
    (IB, "simple"): {"clarification": 28, "agentic": 46}, (IB, "complex"): {"clarification": 124, "agentic": 172}}
CELL_SPLIT = {(PA, "simple"): (438, 62, 125), (PA, "complex"): (66, 10, 19), (CMP, "simple"): (51, 7, 14), (CMP, "complex"): (229, 33, 66),
              (REG, "simple"): (229, 33, 66), (REG, "complex"): (44, 6, 12), (CD, "simple"): (52, 7, 15), (CD, "complex"): (207, 30, 59),
              (IB, "simple"): (52, 7, 15), (IB, "complex"): (207, 30, 59)}
OOS_SPLIT, QUICK_SPLIT = (336, 48, 96), (189, 27, 54)
LEAK_SPLIT = (126, 18, 36)
LEAK_TYPES = {"prompt_injection": 90, "jailbreak": 20, "fraud_or_illegal": 30, "data_extraction": 25, "social_engineering_or_abuse": 15}
BORDER = {"prompt_injection": 2, "jailbreak": 2, "fraud_or_illegal": 16, "data_extraction": 10, "social_engineering_or_abuse": 6}
CLAR_SLOTS = {
    PA: {("product", "missing"): 50, ("field", "missing"): 9, ("coverage", "missing"): 8, ("product", "ambiguous"): 25, ("field", "ambiguous"): 4, ("coverage", "ambiguous"): 4},
    CMP: {("product", "missing"): 45, ("field", "missing"): 10, ("product", "ambiguous"): 22, ("field", "ambiguous"): 5},
    REG: {("topic", "missing"): 8, ("date_reference", "missing"): 15, ("topic", "ambiguous"): 6, ("date_reference", "ambiguous"): 5},
    CD: {("client_profile", "missing"): 45, ("message_goal", "missing"): 40, ("product", "missing"): 10, ("client_profile", "ambiguous"): 22, ("message_goal", "ambiguous"): 20, ("product", "ambiguous"): 5},
    IB: {("client_profile", "missing"): 55, ("product", "missing"): 45, ("client_profile", "ambiguous"): 27, ("product", "ambiguous"): 25}}
CD_SPLIT_SRC = {"simple": {"train": (26, 26), "validation": (4, 3)}, "complex": {"train": (104, 103), "validation": (15, 15)}}
PAIRS = {"missing_info": 200, "complexity": 90, "feature": 80, "leaked": 80}
PAIR_SPLIT = {"missing_info": (140, 20, 40), "complexity": (63, 9, 18), "feature": (56, 8, 16), "leaked": (56, 8, 16)}
QA_Q = {  # (doc, split): (single_value, conditional, multi_fact, absent)
    ("zurich_salute", "train"): (128, 80, 48, 64), ("generali_immagina_adesso", "train"): (212, 132, 80, 106),
    ("zurich_salute", "validation"): (30, 19, 11, 15), ("generali_immagina_adesso", "validation"): (30, 19, 11, 15),
    ("zurich_impresa", "test"): (200, 125, 75, 100)}
SC = ["self_contained", "follow_up", "no_policy", "ambiguous_product", "slot_clarified"]
SC_TOTAL = [1200, 900, 360, 300, 240]
MODS = {"context_conflict": 120, "mixed_features": 150, "innocent_imperative": 60, "negation_or_exception": 150, "long_preamble": 180,
        "telegraphic": 240, "code_mixed": 150, "typos_abbreviations": 360}
STYLE_TOTAL = {"formal": 1050, "informal": 1350, "paraphrase": 600}
REQ = {PA: ["insurer", "product", "field", "coverage"], CMP: ["insurer", "product", "field", "coverage"], REG: ["topic"],
       CD: ["product", "client_profile", "message_goal"], IB: ["product", "client_profile"]}
REG_TOPICS = ["reclami e tempi di risposta", "consegna del set informativo e del DIP", "obblighi IDD di adeguatezza", "privacy e consenso", "conservazione della documentazione",
              "diritto di recesso e ripensamento", "prescrizione dei diritti", "adempimenti IVASS", "conflitto di interessi", "vendita a distanza", "adeguatezza e target market",
              "antiriciclaggio e identificazione del cliente", "mediazione e risoluzione delle controversie", "obblighi di formazione e aggiornamento", "trasparenza e comunicazioni al cliente"]


class Rec(dict):
    __getattr__ = dict.get

    def __setattr__(self, k, v):
        self[k] = v


RECS = []


def new(**kw):
    r = Rec(kw)
    r["idx"] = len(RECS)
    r.setdefault("pair", None); r.setdefault("modifiers", []); r.setdefault("slot_kind", None); r.setdefault("bundle", None)
    RECS.append(r)
    return r


# ----------------------------------------------------------------------------- 1. skeleton of the 3,000 router records
def blocks(cell):
    f, x = cell
    out = []
    for si, sp in enumerate(SPL):
        n = CELL_SPLIT[cell][si]
        if f == PA:
            if sp == "test":
                out.append((sp, "zurich_impresa", n))
            else:
                out += [(sp, "zurich_salute", n - n // 2), (sp, "generali_immagina_adesso", n // 2)]
        elif f == CD:
            if sp == "test":
                out.append((sp, "zurich_impresa", n))
            else:
                a, b = CD_SPLIT_SRC[x][sp]; out += [(sp, "zurich_salute", a), (sp, "generali_immagina_adesso", b)]
        elif f == IB:
            out.append((sp, IBIP_DOC[sp], n))
        elif f == CMP:
            out.append((sp, "compare", n))
        else:
            out.append((sp, "none", n))
    return out


def build_skeleton():
    for cell, routes in GRID.items():
        f, x = cell
        bl = blocks(cell)
        rn = list(routes)
        M = round_matrix([b[2] for b in bl], [routes[r] for r in rn])
        for bi, (sp, src, n) in enumerate(bl):
            for ri, r in enumerate(rn):
                for _ in range(M[bi, ri]):
                    new(split=sp, feature=f, complexity=x, cell=f"{f}|{x}", route=r, source=src, scope="in_scope", kind="core")
    # out of scope (plain, near miss, leak) and quick replies
    plain_split = [a - b for a, b in zip(OOS_SPLIT, LEAK_SPLIT)]
    near = lr(135, plain_split)
    for si, sp in enumerate(SPL):
        for k in range(plain_split[si]):
            new(split=sp, feature="none", complexity=None, cell="oos", route="refuse", source="none", scope="out_of_scope", kind="near_miss" if k < near[si] else "plain")
    lt = list(LEAK_TYPES)
    M = round_matrix([LEAK_TYPES[t] for t in lt], list(LEAK_SPLIT))
    BM = round_matrix([BORDER[t] for t in lt], list(lr(36, [25, 4, 7])), ub=M)
    nb = M - BM
    obv = round_matrix([72, 72], [int(v) for v in nb.reshape(-1)])
    for ti, t in enumerate(lt):
        for si, sp in enumerate(SPL):
            diffs = ["borderline"] * int(BM[ti, si]) + ["obvious"] * int(obv[0, ti * 3 + si]) + ["subtle"] * int(obv[1, ti * 3 + si])
            for d in diffs:
                new(split=sp, feature="none", complexity=None, cell="oos", route="refuse", source="none", scope="out_of_scope", kind="leak",
                    leak={"type": t, "difficulty": d, "appended": False})
    qt = ["greeting", "thanks", "goodbye", "acknowledgement", "capability"]
    M = round_matrix([54] * 5, list(QUICK_SPLIT))
    for ti, t in enumerate(qt):
        for si, sp in enumerate(SPL):
            for _ in range(M[ti, si]):
                new(split=sp, feature="none", complexity=None, cell="quick", route="quick_reply", source="none", scope="quick_reply", kind=t)
    # appended injections: 60 of the 90 prompt_injection leaks (borderline ones stay standalone)
    for sp, n in zip(SPL, lr(60, [63, 9, 18])):
        pool = [r for r in RECS if r.leak and r.leak["type"] == "prompt_injection" and r.split == sp and r.leak["difficulty"] != "borderline"]
        for r in pick(pool, n):
            r.leak["appended"] = True
    # leaks with a legitimate history: 30%
    for r in pick([r for r in RECS if r.leak], 54):
        r["leak_history"] = True
    # slots of clarification records
    for f, dist in CLAR_SLOTS.items():
        recs = [r for r in RECS if r.feature == f and r.route == "clarification"]
        labels = [k for k, v in dist.items() for _ in range(v)]
        assert len(labels) == len(recs), (f, len(labels), len(recs))
        rng.shuffle(labels)
        for r, lab in zip(recs, labels):
            r.slot_kind = lab
    # regulatory: date_reference needed in about 25% of requests
    regs = [r for r in RECS if r.feature == REG]
    need = [r for r in regs if r.slot_kind and r.slot_kind[0] == "date_reference"]
    rest = [r for r in regs if r not in need]
    for r in need + pick(rest, round(0.25 * len(regs)) - len(need)):
        r["needs_date"] = True
    for r in regs:
        r["topic"] = rng.choice(REG_TOPICS)
    # IBIP: product named in the query (2/3) or only selected (1/3)
    ibs = [r for r in RECS if r.feature == IB and not (r.slot_kind and r.slot_kind[0] == "product")]
    modes = ["selected"] * (len(ibs) // 3) + ["name"] * (len(ibs) - len(ibs) // 3)
    rng.shuffle(modes)
    for r, m in zip(ibs, modes):
        r["ibip_mode"] = m
    # client profiles for drafting and IBIP
    for r in RECS:
        if r.feature in (CD, IB):
            r["profile_id"] = rng.choice(PROFILES)["profile_id"]
            if r.feature == CD:
                r["goal"] = rng.choice(["spiegare", "sollecitare", "rifiutare", "proporre"])
    assert len(RECS) == 3000, len(RECS)


# ----------------------------------------------------------------------------- 2. contrastive pairs (book 7.2)
PAIR_N = 0


def pair(a, b, ptype):
    global PAIR_N
    PAIR_N += 1
    a.pair = {"id": PAIR_N, "type": ptype, "role": "a"}
    b.pair = {"id": PAIR_N, "type": ptype, "role": "b"}


def free(pred):
    return [r for r in RECS if not r.pair and pred(r)]


def build_pairs():
    # leaked pairs: 44 injection+valid, 36 borderline+sibling
    inj = [lr(44, [56, 8, 16])[i] for i in range(3)]
    inj = [31, 4, 9]
    bor = [25, 4, 7]
    for si, sp in enumerate(SPL):
        for kind, n in (("inj", inj[si]), ("bor", bor[si])):
            if kind == "inj":
                leaks = pick(free(lambda r: r.leak and r.split == sp and r.leak["appended"]), n)
                npa = n // 2 if sp != "validation" else 2
                if sp == "train":
                    npa = 16
                if sp == "test":
                    npa = 5
            else:
                leaks = pick(free(lambda r: r.leak and r.split == sp and r.leak["difficulty"] == "borderline"), n)
                npa = 0
            partners = []
            pa_pool = free(lambda r: r.cell == f"{PA}|simple" and r.route == "lightweight" and r.split == sp)
            partners += pick(pa_pool, npa)
            taken = set(id(p) for p in partners)
            reg_pool = free(lambda r: r.cell == f"{REG}|simple" and r.route == "lightweight" and r.split == sp and id(r) not in taken)
            partners += pick(reg_pool, n - npa)
            for L, V in zip(leaks, partners):
                pair(V, L, "leaked")
    # complexity pairs: PA simple lightweight (one product) + comparison complex agentic (two products and a criterion)
    for si, sp in enumerate(SPL):
        n = PAIR_SPLIT["complexity"][si]
        bs = pick(free(lambda r: r.cell == f"{CMP}|complex" and r.route == "agentic" and r.split == sp), n)
        as_ = pick(free(lambda r: r.cell == f"{PA}|simple" and r.route == "lightweight" and r.split == sp), n)
        for A, B in zip(as_, bs):
            pair(A, B, "complexity")
    # feature pairs: PA simple lightweight + client drafting agentic (same product)
    for si, sp in enumerate(SPL):
        n = PAIR_SPLIT["feature"][si]
        for src in sorted({r.source for r in RECS if r.feature == PA and r.split == sp}):
            k = n // len(sorted({r.source for r in RECS if r.feature == PA and r.split == sp})) + (1 if src == "zurich_salute" and n % 2 and sp != "test" else 0)
            if sp == "test":
                k = n
            As = pick(free(lambda r: r.cell == f"{PA}|simple" and r.route == "lightweight" and r.split == sp and r.source == src), k)
            Bs = pick(free(lambda r: r.feature == CD and r.route == "agentic" and r.split == sp and r.source == src), k)
            for A, B in zip(As, Bs):
                pair(A, B, "feature")
    # missing_info pairs: clarification record + the complete version
    feats = [PA, CMP, REG, CD, IB]
    ub = np.array([[len([r for r in RECS if r.feature == f and r.route == "clarification" and r.split == sp and not r.pair]) for sp in SPL] for f in feats])
    M = round_matrix([39, 32, 13, 56, 60], list(PAIR_SPLIT["missing_info"]), ub=ub)
    for fi, f in enumerate(feats):
        for si, sp in enumerate(SPL):
            cl = pick(free(lambda r: r.feature == f and r.route == "clarification" and r.split == sp), int(M[fi, si]))
            for C in cl:
                cands = free(lambda r: r.cell == C.cell and r.route in ("lightweight", "agentic") and r.split == sp and r.source == C.source)
                P = rng.choice(cands)
                pair(P, C, "missing_info")
    n_pairs = collections.Counter(r.pair["type"] for r in RECS if r.pair)
    assert n_pairs == {"missing_info": 400, "complexity": 180, "feature": 160, "leaked": 160}, n_pairs


# ----------------------------------------------------------------------------- 3. Dataset 2: QA bundles with caps
BUNDLES = []


def new_bundle(**kw):
    b = {"routers": [], "qa": None, "chunks": [], "history_chunk": None, "key": len(BUNDLES)}
    b.update(kw)
    BUNDLES.append(b)
    return b


def ladder(doc, split):
    s, c, m, a = QA_Q[(doc, split)]
    base = 3 if split != "test" else 2
    nval = sum(1 for k, v in CAT.items() if v["doc_id"] == doc and v["pool"] == POOL_OF[split] and v["has_value"])
    need = s + c
    steps = [(base, 0.7, "0: base cap, 70% of capacity"), (base, 1.0, "1: base cap, 100% of capacity"), (base + 1, 1.0, f"2: QA cap {base+1}"), (base + 2, 1.0, f"3: QA cap {base+2}")]
    for i, (cap, frac, label) in enumerate(steps):
        if need <= frac * nval * cap:
            return i, cap, label, nval, need
    raise RuntimeError(f"ladder exhausted for {doc} {split}: need {need}, value chunks {nval}")


def draw_qa(doc, split, level, init_sec):
    base = 3 if split != "test" else 2
    cap = base + max(0, level - 1)
    ncap = lambda lv: base + max(0, lv - 1)
    s, c, m, a = QA_Q[(doc, split)]
    total = s + c + m + a
    sec_cap = 80 if split == "test" else (int(0.2 * total) if split == "train" else 10**9)  # validation is one held-out section
    chunks = [v for v in CAT.values() if v["doc_id"] == doc and v["pool"] == POOL_OF[split]]
    chunks.sort(key=lambda v: v["chunk_id"])
    by_sec = collections.defaultdict(list)
    for v in chunks:
        by_sec[v["top_section"]].append(v)
    uses = collections.Counter()
    sec_n = collections.Counter(init_sec)
    out = []

    def draw_one(cands, weight_by_all=True):
        cs = collections.defaultdict(list)
        for v in cands:
            if uses[v["chunk_id"]] < cap and sec_n[v["top_section"]] < sec_cap:
                cs[v["top_section"]].append(v)
        if not cs:
            return None
        sec = min(cs, key=lambda s_: (sec_n[s_] / max(len(by_sec[s_]), 1), s_))
        mn = min(uses[v["chunk_id"]] for v in cs[sec])
        v = rng.choice([x for x in cs[sec] if uses[x["chunk_id"]] == mn])
        return v

    for qtype, need in (("conditional", c), ("single_value", s)):
        cands = [v for v in chunks if v["has_value"] and (v["has_condition"] or qtype == "single_value")]
        for _ in range(need):
            v = draw_one(cands)
            if v is None:
                return None
            out.append({"qtype": qtype, "chunks": [v["chunk_id"]], "fact_index": uses[v["chunk_id"]]})
            uses[v["chunk_id"]] += 1; sec_n[v["top_section"]] += 1
    order = {v["chunk_id"]: i for i, v in enumerate(chunks)}
    for _ in range(m):
        lst = [v for v in chunks if "multi_fact" in v["usable_for"] and not v["has_value"]] or [v for v in chunks if "multi_fact" in v["usable_for"]]
        v = draw_one(lst) or draw_one([v for v in chunks if "multi_fact" in v["usable_for"]])
        if v is None:
            return None
        group = [v]
        want = 2 if rng.random() < 2 / 3 else 3
        sib = [x for x in by_sec[v["top_section"]] if x["chunk_id"] != v["chunk_id"] and uses[x["chunk_id"]] < cap]
        sib.sort(key=lambda x: (abs(order[x["chunk_id"]] - order[v["chunk_id"]]), x["chunk_id"]))
        group += sib[: want - 1]
        if len(group) < 2:
            return None
        for g in group:
            out.append({"_skip": True}) if False else None
            uses[g["chunk_id"]] += 1
        sec_n[v["top_section"]] += 1
        out.append({"qtype": "multi_fact", "chunks": [g["chunk_id"] for g in group], "fact_index": 0})
    return out, uses, sec_n


def plan_qa():
    state = {}
    for (doc, split), (s, c, m, a) in QA_Q.items():
        # absent questions first: they count toward the section spread
        topics = [t for t in ABSENT if t["doc_id"] == doc and t["split"] == split]
        assert topics, (doc, split)
        quota = a
        if quota > 5 * len(topics):
            note(f"absent quota of {doc} {split} reduced from {quota} to {5*len(topics)}")
            quota = 5 * len(topics)
        counts = lr(quota, [1] * len(topics))
        absent_specs = []
        for t, k in zip(sorted(topics, key=lambda t: t["topic"]), counts):
            secchunks = sorted([v for v in CAT.values() if v["doc_id"] == doc and v["pool"] == POOL_OF[split] and v["top_section"] == t["expected_section"]], key=lambda v: v["chunk_id"])
            assert len(secchunks) >= 2, (doc, t["expected_section"])
            for angle in range(k):
                absent_specs.append((t, angle + 1, rng.sample(secchunks, 2)))
        init_sec = collections.Counter()  # absent questions have no source section: the spread cap counts answerable questions only
        L0, cap0, label0, nval, need = ladder(doc, split)
        res = None
        for lv in range(L0, 4):
            for _attempt in range(40):
                res = draw_qa(doc, split, lv, init_sec)
                if res is not None:
                    break
            if res is not None:
                level = lv
                break
        if res is None:
            raise RuntimeError(f"cannot satisfy QA quota for {doc} {split}")
        out, uses, sec_n = res
        base = 3 if split != "test" else 2
        capv = base + max(0, level - 1)
        state[f"{doc}|{split}"] = {"cap_level": level, "qa_cap": capv, "value_chunks": nval, "demand_value": need,
                                   "label": label0 if level == L0 else f"{level}: QA cap {capv}"}
        if level > L0:
            note(f"QA cap for {doc} {split}: capacity ladder said step {L0}, drawing (section spread or conditional-chunk supply) forced step {level} (cap {capv})")
        for o in out:
            bb = new_bundle(btype="qa", doc=doc, split=split, chunks=o["chunks"], family=fam_doc(doc, split))
            bb["qa"] = {"question_type": o["qtype"], "gold": list(o["chunks"]), "fact_index": o["fact_index"], "expected_behavior": "answer"}
        for t, angle, ctx in absent_specs:
            bb = new_bundle(btype="qa", doc=doc, split=split, chunks=[x["chunk_id"] for x in ctx], family=fam_doc(doc, split))
            bb["qa"] = {"question_type": "absent", "gold": [], "topic": t["topic"], "angle": angle, "terms": t["terms_searched"],
                        "expected_section": t["expected_section"], "expected_behavior": "absent"}
    # QA modifiers per split
    qs = [b for b in BUNDLES if b["btype"] == "qa"]
    for sp, (ni, nt, ntel) in zip(SPL, zip(lr(600, [850, 150, 500]), lr(150, [850, 150, 500]), lr(150, [850, 150, 500]))):
        bs = [b for b in qs if b["split"] == sp]
        rng.shuffle(bs)
        for b in bs:
            b["qa"]["noise_tags"] = []
        for b in bs[:ni]:
            b["qa"]["noise_tags"].append("informal")
        for b in bs[ni:ni + nt]:
            b["qa"]["noise_tags"].append("typo")
        for b in bs[ni + nt:ni + nt + ntel]:
            b["qa"]["noise_tags"].append("telegraphic")
        ans = [b for b in bs if b["qa"]["question_type"] != "absent"]
        for b in rng.sample(ans, round(0.4 * len(ans))):
            b["qa"]["noise_tags"].append("hard_negative")
    return state


# ----------------------------------------------------------------------------- 4. router records onto bundles
RO_USE = collections.Counter()  # (chunk_id, split) -> router-only uses
CMP_PAIR_USE = collections.Counter()
FIELD_CAT = {}


def chunk_fields(cid):
    return set(CAT[cid]["fields_found"])


def ro_cap(split):
    return 3 if split != "test" else 2


def draw_value_chunk(doc, split, multi=False):
    pool = [v for v in CAT.values() if v["doc_id"] == doc and v["pool"] == POOL_OF[split] and (v["has_value"] if not multi else "multi_fact" in v["usable_for"])]
    pool = [v for v in pool if RO_USE[(v["chunk_id"], split)] < ro_cap(split)]
    assert pool, f"no router-only capacity {doc} {split}"
    mn = min(RO_USE[(v["chunk_id"], split)] for v in pool)
    return rng.choice(sorted([v for v in pool if RO_USE[(v["chunk_id"], split)] == mn], key=lambda v: v["chunk_id"]))


def attach_pa():
    units = {}
    for r in RECS:
        if r.pair and r.pair["type"] in ("complexity",):
            continue  # handled with the comparison bundles
        if r.pair and any(m.feature == CMP for m in RECS if m.pair and m.pair["id"] == r.pair["id"]):
            continue
        if r.pair:
            members = [m for m in RECS if m.pair and m.pair["id"] == r.pair["id"]]
            if not any(m.feature == PA for m in members):
                continue  # pair without a chunk-based member: written without a document
            units.setdefault(("p", r.pair["id"]), members)
        elif r.feature == PA:
            units[("s", r.idx)] = [r]
    items = [sorted(v, key=lambda x: x.idx) for k, v in units.items()]
    items.sort(key=lambda rs: (-len(rs), rs[0].idx))
    qa_by = collections.defaultdict(list)
    for b in BUNDLES:
        if b["btype"] == "qa" and b["qa"]["question_type"] != "absent":
            qa_by[(b["doc"], b["split"])].append(b)
    nro = 0
    for rs in items:
        # doc of the PA record(s)
        pa = [x for x in rs if x.feature == PA][0]
        doc, sp = pa.source, pa.split
        cx = pa.complexity
        ok_types = ("single_value", "conditional") if cx == "simple" else ("multi_fact", "conditional")
        cands = [b for b in qa_by[(doc, sp)] if b["qa"]["question_type"] in ok_types and len(b["routers"]) + len(rs) <= 2]
        if cands:
            mn = min(len(b["routers"]) for b in cands)
            b = rng.choice([x for x in cands if len(x["routers"]) == mn])
        else:
            nro += 1
            if cx == "simple":
                v = draw_value_chunk(doc, sp)
                ch = [v["chunk_id"]]
            else:
                v = draw_value_chunk(doc, sp, multi=True)
                sib = [x for x in CAT.values() if x["doc_id"] == doc and x["top_section"] == v["top_section"] and x["chunk_id"] != v["chunk_id"] and x["pool"] == v["pool"]]
                sib.sort(key=lambda x: (abs(x["page"] - v["page"]), x["chunk_id"]))
                ch = [v["chunk_id"], sib[0]["chunk_id"]]
            for c_ in ch:
                RO_USE[(c_, sp)] += 1
            b = new_bundle(btype="router_only", doc=doc, split=sp, chunks=ch, family=fam_doc(doc, sp))
        for x in rs:
            x.bundle = b["key"]
            b["routers"].append(x)
    if nro:
        note(f"{nro} product-analysis units had no free QA bundle and went into router-only bundles")


def plan_comparison():
    fields_by_split = collections.defaultdict(dict)
    for r in COMP:
        fields_by_split[r["split"]][r["field"]] = r
    split_docs = {"train": ("zurich_salute", "train_pool", "generali_immagina_adesso", "train_pool"),
                  "validation": ("zurich_salute", "validation_pool", "generali_immagina_adesso", "validation_pool"),
                  "test": ("zurich_impresa", "test_pool", "generali_immagina_adesso", "train_pool")}
    pair_limit = collections.Counter()
    ro_cmp = collections.Counter()

    def draw_pair(sp, need_fields):
        da, pa_, db, pb_ = split_docs[sp]
        best = None
        fields = sorted(fields_by_split[sp])
        order = fields[:]
        rng.shuffle(order)
        # round-robin over fields, least used first
        order.sort(key=lambda f: ro_cmp[(sp, f)])
        for f in order:
            A = [v for v in CAT.values() if v["doc_id"] == da and v["pool"] == pa_ and f in v["fields_found"] and RO_USE[(v["chunk_id"], sp)] < ro_cap(sp)]
            B = [v for v in CAT.values() if v["doc_id"] == db and v["pool"] == pb_ and f in v["fields_found"] and RO_USE[(v["chunk_id"], sp)] < ro_cap(sp)]
            if not A or not B:
                continue
            A.sort(key=lambda v: (RO_USE[(v["chunk_id"], sp)], rng.random()))
            B.sort(key=lambda v: (RO_USE[(v["chunk_id"], sp)], rng.random()))
            for a in A[:12]:
                for b in B[:12]:
                    key = (sp, f, a["coverage"], b["coverage"])
                    if pair_limit[key] >= 6:
                        continue
                    common = set(a["fields_found"]) & set(b["fields_found"])
                    if need_fields and len(common) < 2:
                        continue
                    return f, a, b, sorted(common), key
        return None

    cmp_units = []
    for r in RECS:
        if r.feature == CMP:
            cmp_units.append(r)
    done = set()
    # complexity pairs first: bundle holds the PA record and the comparison record
    for r in cmp_units:
        if r.pair and r.pair["type"] == "complexity" and r.idx not in done:
            partner = [x for x in RECS if x.pair and x.pair["id"] == r.pair["id"] and x.idx != r.idx][0]
            res = draw_pair(r.split, True) or draw_pair(r.split, False)
            assert res, "comparison capacity exhausted"
            f, a, b, common, key = res
            pair_limit[key] += 1; ro_cmp[(r.split, f)] += 1
            for c_ in (a["chunk_id"], b["chunk_id"]):
                RO_USE[(c_, r.split)] += 1
            # the PA record is about the chunk of its own document
            ch_pa = a if a["doc_id"] == partner.source else b
            bd = new_bundle(btype="router_only", doc="compare", split=r.split, chunks=[a["chunk_id"], b["chunk_id"]], family=None, cmp_field=f, cmp_common=common)
            bd["pa_chunk"] = ch_pa["chunk_id"]
            for x in (partner, r):
                x.bundle = bd["key"]; bd["routers"].append(x); done.add(x.idx)
    for r in cmp_units:
        if r.idx in done:
            continue
        # unpaired or missing_info pair (two comparison records share one bundle)
        grp = [r] if not r.pair else [x for x in RECS if x.pair and x.pair["id"] == r.pair["id"]]
        if any(x.idx in done for x in grp):
            continue
        res = draw_pair(r.split, r.complexity == "complex") or draw_pair(r.split, False)
        assert res, "comparison capacity exhausted"
        f, a, b, common, key = res
        pair_limit[key] += 1; ro_cmp[(r.split, f)] += 1
        for c_ in (a["chunk_id"], b["chunk_id"]):
            RO_USE[(c_, r.split)] += 1
        bd = new_bundle(btype="router_only", doc="compare", split=r.split, chunks=[a["chunk_id"], b["chunk_id"]], family=None, cmp_field=f, cmp_common=common)
        for x in grp:
            x.bundle = bd["key"]; bd["routers"].append(x); done.add(x.idx)


# ----------------------------------------------------------------------------- 5. families, no-document bundles
def seed_cell(r):
    if r.cell == "oos":
        return "oos"
    if r.cell == "quick":
        return "quick"
    m = {REG: "reg", CD: "cd", IB: "ibip"}[r.feature]
    return f"{m}_{r.complexity}"


def assign_families():
    """Whole seed families go to one split. Records of pairs inherit the family of one member."""
    by_cell = collections.defaultdict(list)
    for r in RECS:
        if r.bundle is None and not r.leak:
            by_cell[seed_cell(r)].append(r)
    fam_split = {}  # seed family -> split
    for cell, recs in by_cell.items():
        seeds = [s for s in SEEDS if s["cell"] == cell]
        counts = {sp: len([r for r in recs if r.split == sp]) for sp in SPL}
        groups = [seeds]
        if cell == "ibip_simple" or cell == "ibip_complex":
            groups = [[s for s in seeds if s["notes"] != "allianz_test_only"], [s for s in seeds if s["notes"] == "allianz_test_only"]]
        elif cell == "oos":
            groups = [[s for s in seeds if s["notes"] == "plain"], [s for s in seeds if s["notes"] == "near_miss"]]
        elif cell == "quick":
            groups = [[s for s in seeds if s["notes"] == t] for t in ["greeting", "thanks", "goodbye", "acknowledgement", "capability"]]
        for g in groups:
            if g and all(s["notes"] == "allianz_test_only" for s in g):
                for s in g:
                    fam_split[s["family"]] = "test"
                continue
            sps = [sp for sp in SPL if counts[sp] > 0 and not (cell.startswith("ibip") and sp == "test")]
            k = lr(len(g), [counts[sp] for sp in sps])
            k = [max(1, x) for x in k]
            while sum(k) > len(g):
                k[k.index(max(k))] -= 1
            i = 0
            gs = g[:]
            rng.shuffle(gs)
            for sp, n in zip(sps, k):
                for s in gs[i:i + n]:
                    fam_split[s["family"]] = sp
                i += n
    # leak families: held-out families only in validation / test
    for s in SEEDS:
        if s["cell"] == "leak":
            fam_split[s["family"]] = s["holdout_split"] or "train"
    # assign records to families of their split, round robin
    for cell, recs in by_cell.items():
        for sp in SPL:
            rs = [r for r in recs if r.split == sp]
            if not rs:
                continue
            if cell == "oos":
                for kind in ("plain", "near_miss"):
                    fams = sorted({s["family"] for s in SEEDS if s["cell"] == cell and s["notes"] == kind and fam_split[s["family"]] == sp})
                    sub = [r for r in rs if r.kind == kind]
                    for i, r in enumerate(sub):
                        r["family"] = fams[i % len(fams)]
                continue
            if cell == "quick":
                for r in rs:
                    fams = sorted({s["family"] for s in SEEDS if s["cell"] == cell and s["notes"] == r.kind and fam_split[s["family"]] == sp})
                    r["family"] = fams[len([x for x in rs if x.get("family") and x.kind == r.kind]) % len(fams)]
                continue
            fams = sorted({s["family"] for s in SEEDS if s["cell"] == cell and fam_split[s["family"]] == sp})
            if cell.startswith("ibip"):
                fams = [f for f in fams if (sp == "test") == any(s["family"] == f and s["notes"] == "allianz_test_only" for s in SEEDS)]
            assert fams, (cell, sp)
            units = {}
            for r in rs:
                units.setdefault(("p", r.pair["id"]) if r.pair else ("s", r.idx), []).append(r)
            for i, (k, grp) in enumerate(sorted(units.items(), key=lambda kv: kv[1][0].idx)):
                fam = fams[i % len(fams)]
                for r in grp:
                    r["family"] = fam
    # leak records: phrasing family from the seeds of their type
    for t in LEAK_TYPES:
        for sp in SPL:
            rs = [r for r in RECS if r.leak and r.leak["type"] == t and r.split == sp]
            fams = sorted({s["family"] for s in SEEDS if s["cell"] == "leak" and s["leak_type"] == t and fam_split[s["family"]] == sp})
            for i, r in enumerate(rs):
                r.leak["phrasing_family"] = fams[i % len(fams)]
                if not r.bundle and not r.family:
                    r["family"] = fams[i % len(fams)]
    # pair members that sit in a reg or leak bundle: family consistency (a pair shares one family)
    for r in RECS:
        if r.pair and r.feature != PA and r.feature != CMP and not r.leak:
            mates = [x for x in RECS if x.pair and x.pair["id"] == r.pair["id"] and x is not r]
            for m in mates:
                if m.family and not r.family:
                    r["family"] = m.family
    return fam_split


def family_of_bundle_records():
    for b in BUNDLES:
        for r in b["routers"]:
            if b["btype"] == "qa" or b["doc"] != "compare":
                r["family"] = b["family"]
            else:
                sp = r.split
                r["family"] = "+".join([fam_doc(d, sp) for d in {"train": ("zurich_salute", "generali_immagina_adesso"), "validation": ("zurich_salute", "generali_immagina_adesso"), "test": ("zurich_impresa", "generali_immagina_adesso")}[sp]])
            if r.pair:
                pass
    # pairs spanning a chunk bundle: every member takes the bundle family
    for b in BUNDLES:
        for r in b["routers"]:
            for m in b["routers"]:
                pass


# ----------------------------------------------------------------------------- 6. scenarios and modifiers
def klass(r):
    if r.cell == "quick":
        return "quick"
    if r.cell == "oos":
        return ("leak_h" if r.get("leak_history") else "leak_n") if r.leak else "oos"
    if r.slot_kind:
        if r.feature == REG:
            return "cl_reg"
        return "cl_prod" if r.slot_kind[0] == "product" else "cl_other"
    if r.feature == REG:
        return "comp_reg"
    return "comp_pa" if r.feature == PA else "comp_pd"


ELIG = {"cl_prod": [0, 0, 1, 1, 0], "cl_other": [1, 1, 0, 0, 0], "cl_reg": [1, 1, 1, 1, 0], "comp_pd": [1, 1, 0, 0, 1], "comp_pa": [1, 1, 0, 0, 1],
        "comp_reg": [1, 1, 1, 1, 1], "oos": [1, 1, 1, 1, 0], "leak_n": [1, 0, 1, 1, 0], "leak_h": [0, 1, 0, 0, 0], "quick": [1, 1, 1, 1, 0]}


def assign_scenarios():
    col_split = round_matrix([SPLIT_N[s] for s in SPL], SC_TOTAL)  # splits x scenarios
    classes = list(ELIG)
    for si, sp in enumerate(SPL):
        recs = [r for r in RECS if r.split == sp]
        size = [len([r for r in recs if klass(r) == c]) for c in classes]
        cols = [int(x) for x in col_split[si]]
        allowed = np.array([ELIG[c] for c in classes])
        T = np.zeros((len(classes), 5))
        for i, c in enumerate(classes):
            w = np.array(ELIG[c], float) * np.array(cols, float)
            T[i] = size[i] * w / w.sum() if w.sum() else 0
        lb = np.zeros((len(classes), 5))
        i_pa = classes.index("comp_pa")
        if sp != "test":
            lb[i_pa, 1] = int(0.55 * size[i_pa])
        M = round_matrix(size, cols, allowed=allowed, target=T, lb=lb)
        for i, c in enumerate(classes):
            rs = [r for r in recs if klass(r) == c]
            labels = [SC[j] for j in range(5) for _ in range(M[i, j])]
            rng.shuffle(labels)
            for r, lab in zip(rs, labels):
                r["scenario"] = lab
    # slot clarified: which slot was answered
    for r in RECS:
        if r.scenario == "slot_clarified":
            opts = {PA: ["product", "product", "field", "coverage"], CMP: ["product"], REG: ["topic"] if not r.needs_date else ["topic", "date_reference"],
                    CD: ["client_profile", "message_goal", "product"], IB: ["client_profile", "product"]}[r.feature]
            r["clarified_slot"] = rng.choice(opts)


PAIR_FORBIDDEN = {"long_preamble", "telegraphic", "mixed_features", "context_conflict", "innocent_imperative", "negation_or_exception"}


def mod_ok(mod, r):
    if r.pair and mod in PAIR_FORBIDDEN:
        return False  # the two queries of a pair stay within 8 words of each other
    inscope = r.scope == "in_scope"
    m = set(r.modifiers)
    if mod == "context_conflict":
        return r.feature == PA and r.scenario == "follow_up" and r.split != "test" and r.bundle is not None
    if mod == "mixed_features":
        return inscope and r.feature in (CD, IB, CMP) and (r.complexity == "complex" or r.route == "clarification") and not (m & {"telegraphic", "long_preamble"})
    if mod == "innocent_imperative":
        return inscope and r.feature in (REG, PA) and r.route in ("lightweight", "agentic") and not (m & {"telegraphic"})
    if mod == "negation_or_exception":
        return inscope and r.feature in (PA, CMP, REG) and not (m & {"telegraphic"})
    if mod == "long_preamble":
        return r.cell != "quick" and not (m & {"telegraphic", "mixed_features"})
    if mod == "telegraphic":
        return (r.scenario == "follow_up" or r.cell in ("oos", "quick") or r.route == "clarification") and not r.leak and not (m & {"long_preamble", "mixed_features", "code_mixed", "innocent_imperative"})
    if mod == "code_mixed":
        return r.cell != "quick" and not (m & {"telegraphic"})
    if mod == "typos_abbreviations":
        return True
    return False


def assign_modifiers():
    # subtle leaks hide in a long preamble
    subtle = [r for r in RECS if r.leak and r.leak["difficulty"] == "subtle" and not r.pair]
    for r in pick(subtle, 40):
        r.modifiers.append("long_preamble")
    for mod, total in MODS.items():
        if mod == "context_conflict":
            per = dict(zip(SPL, lr(total, [2100, 300, 0] if False else [2100, 300, 1])[:2] + [0]))
            per = {"train": round(total * 2100 / 2400), "validation": total - round(total * 2100 / 2400), "test": 0}
        else:
            per = dict(zip(SPL, lr(total, [2100, 300, 600])))
        if mod == "long_preamble":
            have = collections.Counter(r.split for r in RECS if "long_preamble" in r.modifiers)
            per = {sp: per[sp] - have[sp] for sp in SPL}
        for sp in SPL:
            pool = [r for r in RECS if r.split == sp and mod_ok(mod, r) and mod not in r.modifiers]
            for r in pick(pool, per[sp]):
                r.modifiers.append(mod)
    # styles: informal first for the typo, telegraphic and code-mixed records
    for sp in SPL:
        recs = [r for r in RECS if r.split == sp]
        tot = dict(zip(STYLE_TOTAL, [0, 0, 0]))
    sty = round_matrix([SPLIT_N[s] for s in SPL], list(STYLE_TOTAL.values()))
    for si, sp in enumerate(SPL):
        recs = [r for r in RECS if r.split == sp]
        left = {"formal": int(sty[si, 0]), "informal": int(sty[si, 1]), "paraphrase": int(sty[si, 2])}
        byp = collections.defaultdict(list)
        for r in recs:
            if r.pair:
                byp[r.pair["id"]].append(r)
        for pid in sorted(byp):
            opts = [k for k, v in left.items() if v >= 2]
            stl = rng.choices(opts, [left[k] for k in opts])[0]
            for m in byp[pid]:
                m["style"] = stl
            left[stl] -= 2
        singles = [r for r in recs if not r.pair]
        rng.shuffle(singles)
        singles.sort(key=lambda r: 0 if set(r.modifiers) & {"typos_abbreviations", "telegraphic", "code_mixed"} else 1)
        for r in singles:
            if set(r.modifiers) & {"typos_abbreviations", "telegraphic", "code_mixed"} and left["informal"] > 0:
                r["style"] = "informal"; left["informal"] -= 1
        rest = [r for r in singles if not r.get("style")]
        labels = [k for k, v in left.items() for _ in range(v)]
        rng.shuffle(labels)
        assert len(labels) == len(rest), (sp, len(labels), len(rest))
        for r, lab in zip(rest, labels):
            r["style"] = lab


# ----------------------------------------------------------------------------- 7. context window, labels, jobs
def dispatcher(scope, feature, complexity, missing):
    if scope == "quick_reply":
        return "quick_reply"
    if scope == "out_of_scope":
        return "refuse"
    if missing:
        return "clarification"
    if feature in (IB, CD):
        return "agentic"
    return "agentic" if complexity == "complex" else "lightweight"


def slots_of(r):
    if r.scope != "in_scope":
        return [], [], {}
    req = list(REQ[r.feature])
    if r.feature == REG and r.needs_date:
        req.append("date_reference")
    non = r.slot_kind
    if non and non[0] == "product" and "insurer" in req:
        req.remove("insurer")
    status = {s: "present" for s in req}
    if non:
        status[non[0]] = non[1]
    return req, [s for s in req if status[s] == "present"], status


def history_chunk_for(r, b):
    sp = r.split
    if r.feature == IB:
        return None
    if b is not None and b["btype"] in ("qa", "router_only") and b["doc"] != "compare":
        doc = b["doc"]
        if "context_conflict" in r.modifiers:
            other = [d for d in DOCS2[sp] if d != doc]
            doc = other[0]
        pool = [v for v in CAT.values() if v["doc_id"] == doc and v["pool"] == POOL_OF[sp] and v["chunk_id"] not in b["chunks"]
                and CHUNKS[v["chunk_id"]]["section_path"] != CHUNKS[b["chunks"][0]]["section_path"]]
    elif b is not None:
        doc = rng.choice(["zurich_salute", "generali_immagina_adesso"]) if sp != "test" else "zurich_impresa"
        pool = [v for v in CAT.values() if v["doc_id"] == doc and v["pool"] == POOL_OF[sp] and v["chunk_id"] not in b["chunks"]]
    else:
        doc = r.source if r.source in INSURER else rng.choice(DOCS2[sp])
        pool = [v for v in CAT.values() if v["doc_id"] == doc and v["pool"] == POOL_OF[sp]]
    pool.sort(key=lambda v: v["chunk_id"])
    return rng.choice(pool)["chunk_id"] if pool else None


def context_of(r, b):
    sp = r.split
    sc = r.scenario
    doc = None
    if r.feature == IB:
        doc = IBIP_DOC[sp]
    elif r.source in INSURER:
        doc = r.source
    elif b is not None and b["doc"] != "compare" and b["doc"] in INSURER:
        doc = b["doc"]
    elif b is not None and b["doc"] == "compare":
        doc = DOCS2[sp][0] if sp != "test" else "zurich_impresa"
    prod_dep = r.feature in (PA, CMP, CD, IB)
    prod_slot = r.slot_kind and r.slot_kind[0] == "product"
    sel = None
    if prod_dep and not prod_slot:
        if sc == "follow_up":
            sel = doc
            if "context_conflict" in r.modifiers:
                sel = [d for d in DOCS2[sp] if d != doc][0]
        elif sc == "slot_clarified":
            sel = None if r.get("clarified_slot") == "product" else doc
        elif r.feature == IB:
            sel = doc if r.get("ibip_mode") == "selected" else (doc if rng.random() < 0.5 else None)
        else:
            sel = doc if rng.random() < 0.6 else None
    elif not prod_dep:
        sel = None if sc != "follow_up" else rng.choice(CORE[sp][:2]) if rng.random() < 0.5 else None
    # available docs
    avail = []
    if sel:
        avail.append(sel)
    core_other = [d for d in CORE[sp] if d != sel]
    for d in core_other:
        if rng.random() < 0.7:
            avail.append(d)
    if doc and doc not in avail and prod_dep and not prod_slot and sc != "no_policy":
        avail.append(doc)
    if r.feature == IB and not prod_slot and IBIP_DOC[sp] not in avail:
        avail.append(IBIP_DOC[sp])
    if r.feature == CMP and sp == "test" and "generali_immagina_adesso" not in avail:
        avail.append("generali_immagina_adesso")
    if sc == "ambiguous_product" or prod_slot:
        chunked = [d for d in avail if d in INSURER] + [d for d in CORE[sp] if d in INSURER and d not in avail]
        for d in CORE[sp]:
            if len([x for x in avail if x in CORE[sp]]) < 2 and d not in avail:
                avail.append(d)
    avail = [d for d in dict.fromkeys(avail)]
    while len([d for d in avail if d in CORE[sp]]) < 1 or (len(avail) < 2 and False):
        avail.append(rng.choice(CORE[sp]))
        avail = [d for d in dict.fromkeys(avail)]
    nd = rng.choices([0, 1, 2], [0.4, 0.4, 0.2])[0]
    avail += [f"decoy_{i+1:02d}" for i in range(nd)]
    if len(avail) < 2:
        avail.append("decoy_01")
    avail.sort()
    return sel, avail, doc


def resolved_keys(r):
    sc = r.scenario
    if sc == "follow_up" and r.feature in (PA, CMP):
        keys = [k for k in ("insurer", "product") if k in REQ[r.feature]]
        if r.rand_drop == "coverage" or "context_conflict" in r.modifiers:
            keys.append("coverage")
        if "context_conflict" in r.modifiers:
            keys = [k for k in keys if k not in ("insurer", "product")] + ["insurer", "product"]
        return keys
    if sc == "follow_up" and r.feature == REG:
        return ["topic"]
    if sc == "follow_up" and r.feature in (CD, IB):
        return ["product"] if not (r.slot_kind and r.slot_kind[0] == "product") else []
    if sc == "slot_clarified":
        cs = r.get("clarified_slot")
        return [cs, "insurer"] if cs == "product" and r.feature in (PA, CMP) else [cs]
    return []


def router_fixed(r, b, qid):
    req, filled, status = slots_of(r)
    labels = {"scope_check": r.scope, "feature": r.feature if r.scope == "in_scope" else "none"}
    if r.scope == "in_scope":
        labels["complexity"] = r.complexity
        labels["missing_info"] = [s for s in req if status[s] != "present"]
    route = dispatcher(r.scope, r.feature, r.complexity, labels.get("missing_info"))
    assert route == r.route, (r, route)
    sel, avail, doc = context_of(r, b)
    ctx_dep = r.scenario in ("follow_up", "slot_clarified") or (r.feature == IB and r.get("ibip_mode") == "selected" and not (r.slot_kind and r.slot_kind[0] == "product"))
    src = []
    if b is not None:
        src = list(b["chunks"]) if b["doc"] != "compare" else (list(b["chunks"]) if r.feature == CMP else [b["pa_chunk"]])
    fixed = {"query_id": qid, "bundle_id": None, "family": r.family, "split": r.split, "labels": labels,
             "support": {"required_slots": req, "filled_slots": filled, "slot_status": status, "expected_route": route, "context_scenario": r.scenario,
                         "context_dependency": bool(ctx_dep), "noise_tags": sorted(r.modifiers), "source_chunk_ids": src, "query_style": r.style,
                         "safety_leak": bool(r.leak), "leak_type": r.leak["type"] if r.leak else None,
                         "leak_difficulty": r.leak["difficulty"] if r.leak else None, "pair_id": None, "verified": False,
                         "generator": GENERATOR, "language": "it"},
             "context": {"selected_doc_id": sel, "available_docs": avail, "resolved_slot_keys": resolved_keys(r)}}
    return fixed


def recipe(r):
    if r.cell == "quick":
        return "quick_reply"
    if r.cell == "oos":
        return "refuse_leaked_unsafe" if r.leak else "refuse_out_of_scope"
    if r.route == "clarification":
        return "clarification_ambiguous_slot" if r.slot_kind[1] == "ambiguous" else "clarification_missing_slot"
    return {(PA, "lightweight"): "lightweight_product_lookup", (CMP, "lightweight"): "lightweight_simple_comparison", (REG, "lightweight"): "lightweight_regulatory_lookup",
            (PA, "agentic"): "agentic_complex_analysis", (CMP, "agentic"): "agentic_comparison", (REG, "agentic"): "agentic_complex_regulatory",
            (CD, "agentic"): "agentic_client_drafting", (IB, "agentic"): "agentic_ibip_screening"}[(r.feature, r.route)]


def few_shot(r, n=3):
    cell = {PA: "pa", CMP: "cmp", REG: "reg", CD: "cd", IB: "ibip"}.get(r.feature)
    if r.cell == "oos":
        cell = "oos"
    if r.cell == "quick":
        cell = "quick"
    if r.leak:
        c = [s for s in SEEDS if s["cell"] == "leak" and s["leak_type"] == r.leak["type"] and s["family"] == r.leak.get("phrasing_family")]
        return [s["text"] for s in c][:n]
    full = cell if cell in ("oos", "quick") else f"{cell}_{r.complexity}"
    own = [s for s in SEEDS if s["cell"] == full and s["family"] == r.family]
    pool = [s for s in SEEDS if s["cell"] == full and not s["notes"] == "allianz_test_only" and s["family"] != r.family]
    if r.split == "test" and r.feature == IB:
        pool = [s for s in SEEDS if s["cell"] == full and s["notes"] == "allianz_test_only"]
    if r.split != "test" and r.feature == IB:
        pool = [s for s in pool if "Allianz" not in s["text"]]
    pool = sorted(pool, key=lambda s: s["seed_id"])
    return [s["text"] for s in own] + [s["text"] for s in rng.sample(pool, min(n - len(own), len(pool)))]


def chunk_payload(cid):
    c = CHUNKS[cid]
    return {k: c[k] for k in ("chunk_id", "doc_id", "insurer", "product", "branch", "page", "section_path", "text")}


def build_jobs():
    # follow-up details drawn once per record
    for r in RECS:
        r["rand_drop"] = "coverage" if rng.random() < 0.7 else "product"
    jobs = []
    # ---- chunk bundles (one bundle per job)
    order = sorted(BUNDLES, key=lambda b: (SPL.index(b["split"]), b["btype"], b["doc"], b["key"]))
    for b in order:
        if not b["routers"] and not b["qa"]:
            continue
        jobs.append({"_kind": "chunk", "bundle": b, "split": b["split"]})
    # ---- bundles without a document: records grouped 10 per call
    nodoc = [r for r in RECS if r.bundle is None]
    # pair units: both members in one job (up to 5 pairs per call)
    pairs = collections.defaultdict(list)
    for r in nodoc:
        if r.pair:
            pairs[r.pair["id"]].append(r)
    gp = collections.defaultdict(list)
    for pid, ms in sorted(pairs.items()):
        gp[(ms[0].split, ms[0].pair["type"], seed_cell(sorted(ms, key=lambda m: m.idx)[0]))].append(sorted(ms, key=lambda m: m.idx))
    for (sp, ptype, sc_), units in sorted(gp.items()):
        queues = collections.defaultdict(list)
        for u in units:
            queues[u[0].family].append(u)
        cur = []
        fams = sorted(queues)
        while any(queues.values()):
            for f in fams:
                if queues[f]:
                    cur.append(queues[f].pop(0))
                    if len(cur) == 5:
                        jobs.append({"_kind": "nodoc", "records": [x for u in cur for x in u], "split": sp, "recipe": f"pairs_{ptype}"}); cur = []
        if cur:
            jobs.append({"_kind": "nodoc", "records": [x for u in cur for x in u], "split": sp, "recipe": f"pairs_{ptype}"})
    nodoc = [r for r in nodoc if not r.pair]
    groups = collections.defaultdict(list)
    for r in nodoc:
        groups[(r.split, recipe(r))].append(r)
    for (sp, rec), rs in sorted(groups.items()):
        queues = collections.defaultdict(list)
        for r in sorted(rs, key=lambda r: r.idx):
            queues[r.family].append([r])
        cur, size = [], 0
        fams = sorted(queues)
        while any(queues.values()):
            for f in fams:
                if queues[f]:
                    grp = queues[f].pop(0)
                    if size + len(grp) > 10:
                        jobs.append({"_kind": "nodoc", "records": cur, "split": sp, "recipe": rec}); cur, size = [], 0
                    cur += grp; size += len(grp)
        if cur:
            jobs.append({"_kind": "nodoc", "records": cur, "split": sp, "recipe": rec})
    jobs.sort(key=lambda j: (SPL.index(j["split"]), j["_kind"], (j["bundle"]["key"] if j["_kind"] == "chunk" else j["records"][0].idx)))
    return jobs


def finalize(jobs):
    qid = qaid = bid = pid = 0
    pair_ids = {}
    out = []
    for jn, j in enumerate(jobs, 1):
        bundle_id = f"b-{jn:06d}"
        if j["_kind"] == "chunk":
            b = j["bundle"]
            recs = []
            chunk_ids = list(b["chunks"])
            hist = None
            if b["qa"]:
                qaid += 1
                q = b["qa"]
                recs.append({"kind": "qa", "fixed": {"qa_id": f"qa-{qaid:06d}", "bundle_id": bundle_id, "family": b["family"], "split": b["split"], "question_type": q["question_type"],
                                                    "noise_tags": q.get("noise_tags", []), "expected_behavior": q["expected_behavior"], "gold_chunk_ids": q["gold"],
                                                    "generator": GENERATOR, "language": "it", "verified": False}, "hints": {k: v for k, v in q.items() if k in ("fact_index", "topic", "angle", "terms", "expected_section")}})
            rs = sorted(b["routers"], key=lambda r: r.idx)
            fam = b["family"]
            for r in rs:
                if b["doc"] == "compare":
                    r["family"] = r["family"] or "+".join(sorted(set(CAT[c]["doc_id"] for c in b["chunks"])))
                else:
                    r["family"] = fam
                if r.scenario in ("follow_up",) and r.feature != IB:
                    r["history_chunk"] = history_chunk_for(r, b)
            for r in rs:
                qid += 1
                fx = router_fixed(r, b, f"orc-{qid:06d}")
                fx["bundle_id"] = bundle_id
                if r.pair:
                    pid_ = pair_ids.setdefault(r.pair["id"], f"pair-{len(pair_ids)+1:04d}")
                    fx["support"]["pair_id"] = pid_
                hints = {"cell": r.cell, "recipe": recipe(r), "feature": r.feature, "slot_kind": r.slot_kind, "needs_date": bool(r.needs_date), "topic": r.topic,
                         "modifiers": r.modifiers, "pair_type": r.pair["type"] if r.pair else None, "pair_role": r.pair["role"] if r.pair else None, "pair_max_word_diff": 8 if r.pair else None}
                if r.leak:
                    hints["leak"] = r.leak
                if r.feature in (CD, IB):
                    hints["profile_id"] = r.profile_id
                    hints["goal"] = r.get("goal")
                    hints["ibip_mode"] = r.get("ibip_mode")
                if r.get("rand_drop"):
                    hints["follow_up_drops"] = r.rand_drop
                recs.append({"kind": "router", "fixed": fx, "hints": hints, "seeds": few_shot(r)})
            hc = [r.get("history_chunk") for r in rs if r.get("history_chunk")]
            job = {"job_id": f"job-{jn:06d}", "bundle_id": bundle_id, "scenario": ("qa_" + b["qa"]["question_type"]) if b["qa"] else ("router_only_" + recipe(rs[0])),
                   "split": b["split"], "records": recs, "chunks": [chunk_payload(c) for c in chunk_ids],
                   "history_chunk": {"chunk_id": hc[0], "text": CHUNKS[hc[0]]["text"]} if hc else None,
                   "pairs": sorted({r.pair["type"] for r in rs if r.pair})}
            if b.get("pa_chunk"):
                job["pa_chunk_id"] = b["pa_chunk"]
            if b.get("cmp_field"):
                job["comparison_hint"] = {"field": b["cmp_field"], "common_fields": b["cmp_common"]}
        else:
            recs = []
            for r in sorted(j["records"], key=lambda r: r.idx):
                if r.scenario == "follow_up" and r.feature != IB and r.cell not in ("oos", "quick", "oos"):
                    r["history_chunk"] = history_chunk_for(r, None) if r.feature != REG or rng.random() < 0.5 else None
                qid += 1
                fx = router_fixed(r, None, f"orc-{qid:06d}")
                fx["bundle_id"] = bundle_id
                if r.pair:
                    pid_ = pair_ids.setdefault(r.pair["id"], f"pair-{len(pair_ids)+1:04d}")
                    fx["support"]["pair_id"] = pid_
                hints = {"cell": r.cell, "recipe": recipe(r), "feature": r.feature, "slot_kind": r.slot_kind, "needs_date": bool(r.needs_date), "topic": r.topic,
                         "modifiers": r.modifiers, "pair_type": r.pair["type"] if r.pair else None, "pair_role": r.pair["role"] if r.pair else None, "pair_max_word_diff": 8 if r.pair else None, "kind": r.kind}
                if r.leak:
                    hints["leak"] = r.leak
                    hints["leak_history"] = bool(r.get("leak_history"))
                if r.feature in (CD, IB):
                    prof = [p for p in PROFILES if p["profile_id"] == r.profile_id][0]
                    hints["profile"] = prof
                    hints["goal"] = r.get("goal")
                    hints["ibip_mode"] = r.get("ibip_mode")
                    hints["product_doc"] = r.source
                if r.scenario == "follow_up" and r.get("history_chunk"):
                    hints["history_chunk_id"] = r.history_chunk
                recs.append({"kind": "router", "fixed": fx, "hints": hints, "seeds": few_shot(r)})
            hcs = [r.get("history_chunk") for r in j["records"] if r.get("history_chunk")]
            job = {"job_id": f"job-{jn:06d}", "bundle_id": bundle_id, "scenario": j["recipe"], "split": j["split"], "records": recs, "chunks": [],
                   "history_chunks": [{"chunk_id": c, "text": CHUNKS[c]["text"]} for c in dict.fromkeys(hcs)], "pairs": sorted({r.pair["type"] for r in j["records"] if r.pair})}
        out.append(job)
    return out


# ----------------------------------------------------------------------------- 8. outputs and assertions
def write_matrix():
    rows = []
    for r in RECS:
        rows.append((r.cell, r.route, klass(r), "scenario", r.scenario, r.split))
        for m in r.modifiers:
            rows.append((r.cell, r.route, klass(r), "modifier", m, r.split))
        rows.append((r.cell, r.route, klass(r), "style", r.style, r.split))
    cnt = collections.Counter(rows)
    with open(PLAN / "compatibility_matrix.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cell", "route", "class", "dimension", "value", "split", "allowed", "planned"])
        for k in sorted(cnt):
            w.writerow(list(k) + ["yes", cnt[k]])
        # forbidden combinations (documented, planned 0)
        for c, el in ELIG.items():
            for j, s in enumerate(SC):
                if not el[j]:
                    w.writerow(["*", "*", c, "scenario", s, "*", "no", 0])
    return cnt


def assertions(jobs, state, fam_split):
    res = []
    def check(name, ok, detail=""):
        res.append((name, bool(ok), detail))
    cs = collections.Counter((r.cell, r.route, r.split) for r in RECS)
    # quotas
    for cell, routes in GRID.items():
        for rt, n in routes.items():
            check(f"quota {cell} {rt}", sum(v for (c, r_, s), v in cs.items() if c == f"{cell[0]}|{cell[1]}" and r_ == rt) == n)
    for cell, sp in CELL_SPLIT.items():
        for si, s in enumerate(SPL):
            check(f"split {cell} {s}", sum(v for (c, r_, ss), v in cs.items() if c == f"{cell[0]}|{cell[1]}" and ss == s) == sp[si])
    check("route mix", collections.Counter(r.route for r in RECS) == {"lightweight": 930, "clarification": 510, "agentic": 810, "refuse": 480, "quick_reply": 270}, str(collections.Counter(r.route for r in RECS)))
    check("scenario totals", [collections.Counter(r.scenario for r in RECS)[s] for s in SC] == SC_TOTAL)
    check("modifier totals", all(sum(1 for r in RECS if m in r.modifiers) == n for m, n in MODS.items()), str({m: sum(1 for r in RECS if m in r.modifiers) for m in MODS}))
    check("style totals", collections.Counter(r.style for r in RECS) == STYLE_TOTAL)
    check("pair examples", sum(1 for r in RECS if r.pair) == 1200 - 300 + 0 if False else sum(1 for r in RECS if r.pair) == 900, str(sum(1 for r in RECS if r.pair)))
    # jobs
    chunk_by_job = {}
    recs_flat = [(j, rec) for j in jobs for rec in j["records"]]
    ids = [rec["fixed"].get("query_id") or rec["fixed"].get("qa_id") for _, rec in recs_flat]
    check("ids unique", len(ids) == len(set(ids)))
    check("record counts", sum(1 for _, r in recs_flat if r["kind"] == "router") == 3000 and sum(1 for _, r in recs_flat if r["kind"] == "qa") == 1500,
          f"router {sum(1 for _, r in recs_flat if r['kind']=='router')} qa {sum(1 for _, r in recs_flat if r['kind']=='qa')}")
    # test isolation
    bad = []
    for j in jobs:
        txt_chunks = [c["doc_id"] for c in j["chunks"]]
        if j["split"] in ("train", "validation"):
            for rec in j["records"]:
                ctx = rec["fixed"].get("context") or {}
                if "zurich_impresa" in txt_chunks or "zurich_impresa" in (ctx.get("available_docs") or []) or "allianz_periodical4life" in (ctx.get("available_docs") or []) \
                        or ctx.get("selected_doc_id") in ("zurich_impresa", "allianz_periodical4life"):
                    bad.append(j["job_id"])
            for c in j["chunks"] + [{"chunk_id": h["chunk_id"], "doc_id": CHUNKS[h["chunk_id"]]["doc_id"]} for h in j.get("history_chunks", [])]:
                if CHUNKS[c["chunk_id"]]["pool"] == "test_pool":
                    bad.append(j["job_id"])
        else:
            for c in j["chunks"]:
                p = CHUNKS[c["chunk_id"]]["pool"]
                if p != "test_pool" and not (j["bundle_id"] and c["doc_id"] == "generali_immagina_adesso" and p == "train_pool" and any(r["hints"].get("feature") == CMP for r in j["records"] if r["kind"] == "router")):
                    bad.append(j["job_id"])
        for rec in j["records"]:
            if rec["kind"] == "router":
                t = json.dumps(rec["seeds"], ensure_ascii=False) if j["split"] != "test" else ""
                if "Allianz" in t:
                    bad.append(j["job_id"])
    check("test isolation", not bad, str(sorted(set(bad))[:5]))
    # held-out sections
    bad = [j["job_id"] for j in jobs if j["split"] == "validation" and any(CHUNKS[c["chunk_id"]]["pool"] != "validation_pool" for c in j["chunks"])]
    bad += [j["job_id"] for j in jobs if j["split"] == "train" and any(CHUNKS[c["chunk_id"]]["pool"] != "train_pool" for c in j["chunks"])]
    check("held-out sections", not bad, str(bad[:5]))
    # families and pairs
    fams = collections.defaultdict(set)
    for j, rec in recs_flat:
        fams[rec["fixed"]["family"]].add(j["split"])
    check("families in one split", all(len(v) == 1 for v in fams.values()), str({k: v for k, v in fams.items() if len(v) > 1}))
    pj = collections.defaultdict(set)
    for j, rec in recs_flat:
        pid = rec["fixed"].get("support", {}).get("pair_id")
        if pid:
            pj[pid].add(j["job_id"])
    check("pairs in one job", all(len(v) == 1 for v in pj.values()))
    # leak held-out families
    hold_bad = [r.idx for r in RECS if r.leak and ((r.split == "train" and "hold" in r.leak["phrasing_family"]) or (r.split != "train" and "hold" not in r.leak["phrasing_family"]))]
    check("held-out leak families", not hold_bad)
    # caps
    uses = collections.Counter()
    for j in jobs:
        for rec in j["records"]:
            if rec["kind"] == "qa":
                for c in rec["fixed"]["gold_chunk_ids"]:
                    uses[(c, j["split"])] += 1
    over = [(k, v) for k, v in uses.items() if v > state["qa"][f"{CHUNKS[k[0]]['doc_id']}|{k[1]}"]["qa_cap"]]
    check("QA caps", not over, str(over[:3]))
    ro = collections.Counter()
    for j in jobs:
        if all(rec["kind"] == "router" for rec in j["records"]) and j["chunks"]:
            for c in j["chunks"]:
                ro[(c["chunk_id"], j["split"])] += 1
    over = [(k, v) for k, v in ro.items() if v > ro_cap(k[1])]
    check("router-only caps", not over, str(over[:3]))
    # labels pass the dispatcher
    ok = True
    for _, rec in recs_flat:
        if rec["kind"] == "router":
            fx = rec["fixed"]; lab = fx["labels"]
            route = dispatcher(lab["scope_check"], lab["feature"], lab.get("complexity"), lab.get("missing_info"))
            ok &= route == fx["support"]["expected_route"]
            if lab["scope_check"] == "in_scope":
                sup = fx["support"]
                ok &= lab["missing_info"] == [s for s in sup["required_slots"] if sup["slot_status"][s] != "present"]
                ok &= sorted(sup["filled_slots"]) == sorted(s for s in sup["required_slots"] if sup["slot_status"][s] == "present")
    check("labels and dispatcher", ok)
    pm = collections.defaultdict(list)
    for j, rec in recs_flat:
        pid = rec["fixed"].get("support", {}).get("pair_id")
        if pid:
            pm[pid].append(rec["fixed"]["support"])
    check("pair members: same style, no length-changing modifier", all(len({x["query_style"] for x in v}) == 1 and not any(set(x["noise_tags"]) & PAIR_FORBIDDEN for x in v) for v in pm.values()))
    check("telegraphic never with preamble or mixed features", all(not ({"telegraphic"} <= set(r.modifiers) and set(r.modifiers) & {"long_preamble", "mixed_features"}) for r in RECS))
    # absent topics
    tcount = collections.Counter(); tsplit = collections.defaultdict(set)
    for j, rec in recs_flat:
        if rec["kind"] == "qa" and rec["fixed"]["question_type"] == "absent":
            t = rec["hints"]["topic"]; d = CHUNKS[j["chunks"][0]["chunk_id"]]["doc_id"]
            tcount[(d, t)] += 1; tsplit[t + d].add(j["split"])
    check("absent topics", max(tcount.values()) <= 5 and all(len(v) == 1 for v in tsplit.values()), str(max(tcount.values())))
    # spread
    spread_bad = []
    for (doc, sp), (s, c, m, a) in QA_Q.items():
        secs = collections.Counter()
        for j, rec in recs_flat:
            if rec["kind"] == "qa" and j["split"] == sp and j["chunks"] and j["chunks"][0]["doc_id"] == doc:
                q = rec["fixed"]
                if q["gold_chunk_ids"]:
                    secs[CHUNKS[q["gold_chunk_ids"][0]]["top_section"]] += 1
        if sp == "validation":
            continue
        lim = 80 if sp == "test" else int(0.2 * (s + c + m + a))
        if max(secs.values()) > lim:
            spread_bad.append((doc, sp, max(secs.values()), lim))
    check("section spread", not spread_bad, str(spread_bad))
    return res


def main():
    build_skeleton(); build_pairs()
    state = {"qa": plan_qa()}
    attach_pa(); plan_comparison()
    # families of chunk-bundle records
    for b in BUNDLES:
        for r in b["routers"]:
            r["family"] = b["family"] or None
    for b in BUNDLES:
        if b["doc"] == "compare":
            for r in b["routers"]:
                r["family"] = "+".join(sorted({fam_doc(CAT[c]["doc_id"], b["split"]) if b["split"] != "test" else CAT[c]["doc_id"] for c in b["chunks"]}))
    fam_split = assign_families()
    # records in bundles keep the bundle family
    for b in BUNDLES:
        for r in b["routers"]:
            if b["doc"] != "compare":
                r["family"] = b["family"]
    assign_scenarios(); assign_modifiers()
    jobs_raw = build_jobs()
    jobs = finalize(jobs_raw)
    write_matrix()
    res = assertions(jobs, state, fam_split)
    with open(PLAN / "jobs.jsonl", "w", encoding="utf-8") as f:
        for j in jobs:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")
    st = {"seed": SEED, "generator": GENERATOR, "n_jobs": len(jobs), "n_router": 3000, "n_qa": 1500,
          "router_by_cell_route_split": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in sorted(collections.Counter((r.cell, r.route, r.split) for r in RECS).items())},
          "router_by_route_split": {f"{k[0]}|{k[1]}": v for k, v in sorted(collections.Counter((r.route, r.split) for r in RECS).items())},
          "qa_by_type_doc_split": {}, "router_by_source_split_feature": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in sorted(collections.Counter((r.source, r.split, r.feature if r.feature != "none" else r.cell) for r in RECS).items())}, "qa_cap_levels": state["qa"], "scenarios": dict(collections.Counter(r.scenario for r in RECS)),
          "modifiers": {m: sum(1 for r in RECS if m in r.modifiers) for m in MODS}, "styles": dict(collections.Counter(r.style for r in RECS)),
          "pairs": dict(collections.Counter(r.pair["type"] for r in RECS if r.pair)), "notes": LOG}
    for j in jobs:
        for rec in j["records"]:
            if rec["kind"] == "qa":
                k = f"{rec['fixed']['question_type']}|{j['chunks'][0]['doc_id']}|{j['split']}"
                st["qa_by_type_doc_split"][k] = st["qa_by_type_doc_split"].get(k, 0) + 1
    json.dump(st, open(PLAN / "STATE.json", "w"), indent=1, ensure_ascii=False)
    lines = ["# Plan assertions (book 16.5)\n", "| check | result | detail |", "| --- | --- | --- |"]
    for n_, ok, d in res:
        lines.append(f"| {n_} | {'PASS' if ok else 'FAIL'} | {d[:150]} |")
    (PLAN / "plan_assertions.md").write_text("\n".join(lines), encoding="utf-8")
    fails = [n_ for n_, ok, d in res if not ok]
    print(f"{len(jobs)} jobs; {len(res)} checks; failures: {fails}")


if __name__ == "__main__":
    main()
