"""Validator (book section 10 + planner interpretations in logs/gate_G2.md) and assembler.
Writer output lines (written fields only; fixed fields are merged from the job by code, so they cannot drift):
  router: {"kind":"router","query_id","query","history":[{"role","text"}],"resolved_slots":{k:v}}
  qa:     {"kind":"qa","qa_id","question","risposta","fonte","gold_value","gold_condition","difficulty"}
  skip:   {"kind":"skip","job_id","reason"}
VALIDATOR_VERSION is written to the manifest."""
import json, re, unicodedata, difflib
VALIDATOR_VERSION = '0.2'   # 0.2: non-blocking 'warn:' check on comparison complexity
try:
    from lingua import Language, LanguageDetectorBuilder
    _det = LanguageDetectorBuilder.from_languages(Language.ITALIAN, Language.ENGLISH, Language.FRENCH, Language.SPANISH, Language.GERMAN).build()
except Exception:
    _det = None
CH = {}
for l in open('chunks/chunks.jsonl'):
    c = json.loads(l); CH[c['chunk_id']] = c
LABEL_WORDS = re.compile(r"\b(in_scope|out_of_scope|quick_reply|missing_info|slot|slots|scope_check|clarification|agentic|lightweight|safety_leak|leak_type|context_scenario|follow_up|self_contained|no_policy|ambiguous_product|slot_clarified|jailbreak|prompt_injection)\b|\bslot\b", re.I)
EN = set("the and with what which is are you your how when where does do can could should would this that have has will not for from of to in on at by an a it be been policy deductible claim claims waiting period cover coverage insurer customer client please thanks thank hello".split())
EN_STRICT = set("the and with what which you your how when does can could should would this that have has will not for from please thanks thank hello is are".split())
EN_TERMS = set("deductible claim claims policy waiting period cover coverage insurer customer broker premium benefit benefits exclusion limit cap".split())
PII = [re.compile(p) for p in [r"[\w.+-]+@[\w-]+\.[\w.]+", r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b", r"(?<!\d)(\+?39)?\s?3\d{2}[\s.-]?\d{6,7}(?!\d)", r"(?<!\d)0\d{1,3}[\s./-]?\d{5,8}(?!\d)"]]
BAD_CHARS = '  \u0085'
def norm(s): return re.sub(r'\s+', ' ', s).strip()
def words(s): return re.findall(r"[\w'’]+", s, re.U)
def nw(s): return len(words(s))
def toks(s): return [unicodedata.normalize('NFC', w).lower().replace('’', "'") for w in words(s)]
def sentences(s): return [x for x in re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ú"«(])', s.strip()) if x.strip()]
def max_run(text, chunk_texts, n=12):
    t = toks(text)
    if len(t) <= n: return False
    grams = set()
    for c in chunk_texts:
        ct = toks(c)
        for i in range(len(ct) - n): grams.add(tuple(ct[i:i+n+1]))
    return any(tuple(t[i:i+n+1]) in grams for i in range(len(t) - n))
PATHS = []
def lang_ok(text, code_mixed, chunk_texts=()):
    w = [x.lower() for x in words(text)]
    en = [x for x in w if x in EN_STRICT]
    known = set(x.lower() for c in chunk_texts for x in words(c)) | set(x.lower() for x in words(' '.join(PATHS)))
    terms = [x for x in w if x in EN_TERMS and x not in known]
    if len(en) >= 2 and len(w) >= 4: return False, 'english sentence'
    if terms and not code_mixed: return False, 'english term without code_mixed modifier'
    if len(terms) > 2: return False, 'more than 2 english terms'
    if _det and len(w) >= 8:
        l = _det.detect_language_of(re.sub(r'(?i)target market|set informativo|key information document|broker|online|software|privacy|email|app', ' ', text))
        if l is not None and l != Language.ITALIAN and not code_mixed: return False, f'language {l.name}'
    return True, ''
def check_text(label, text, errs, code_mixed=False, maxw=None, minw=None, chunk_texts=(), allow_empty=False):
    if not isinstance(text, str) or (not text.strip() and not allow_empty):
        errs.append(f'{label}: empty or not a string'); return
    if any(c in text for c in BAD_CHARS): errs.append(f'{label}: forbidden char')
    n = nw(text)
    if maxw and n > maxw: errs.append(f'{label}: {n} words > {maxw}')
    if minw and n < minw: errs.append(f'{label}: {n} words < {minw}')
    if LABEL_WORDS.search(text): errs.append(f'{label}: label/scenario name in text ({LABEL_WORDS.search(text).group(0)})')
    ok, why = lang_ok(text, code_mixed, chunk_texts)
    if not ok: errs.append(f'{label}: {why}')
    for p in PII:
        if p.search(text): errs.append(f'{label}: personal-data pattern')
    if chunk_texts and max_run(text, chunk_texts): errs.append(f'{label}: >12-word run copied from a chunk')
CRIT = re.compile(r"\b(conviene|convenient\w*|meglio|migliore|preferibil\w*|consigli\w*|vantaggios\w*|vale la pena|più adatt\w*)\b", re.I)
def comparison_warning(job, f, q):
    """non-blocking: comparison labelled complex needs 2+ fields or a criterion; simple must have neither (book s.4)."""
    l = f['labels']
    if l.get('feature') != 'comparison' or l.get('scope_check') != 'in_scope' or not isinstance(q, str): return None
    fields = [x.lower() for x in (job.get('comparison_hint') or {}).get('common_fields', [])]
    nf = sum(1 for x in fields if x in q.lower()); crit = bool(CRIT.search(q))
    if l.get('complexity') == 'complex' and nf < 2 and not crit and f['support']['context_scenario'] not in ('follow_up', 'slot_clarified'):
        return 'warn: comparison labelled complex but the query names fewer than 2 fields and no criterion'
    if l.get('complexity') == 'simple' and (nf >= 2 or crit): return 'warn: comparison labelled simple but the query names 2+ fields or a criterion'
    return None
def pair_diff(a, b):
    x, y = words(a.lower()), words(b.lower())
    sm = difflib.SequenceMatcher(None, x, y, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != 'equal')

def validate_record(job, rec, w, all_written=None):
    """returns list of error strings"""
    errs = []; f = rec['fixed']; h = rec['hints']
    gold = [CH[c]['text'] for c in (f.get('gold_chunk_ids') or [])] if rec['kind'] == 'qa' else [CH[c]['text'] for c in f['support']['source_chunk_ids']]
    alltexts = [c['text'] for c in job['chunks']] + [(job.get('history_chunk') or {}).get('text', '')]
    alltexts = [t for t in alltexts if t]
    PATHS[:] = [c.get('section_path') or '' for c in job['chunks']]
    if rec['kind'] == 'router':
        s = f['support']; mods = set(s['noise_tags']); cm = 'code_mixed' in mods
        q = w.get('query')
        tele = 'telegraphic' in mods
        check_text('query', q, errs, cm, maxw=60, minw=2, chunk_texts=alltexts)
        cw = comparison_warning(job, f, q)
        if cw: errs.append(cw)
        if tele and isinstance(q, str) and not (2 <= nw(q) <= 4): errs.append(f'query: telegraphic needs 2-4 words, has {nw(q)}')
        hist = w.get('history')
        if not isinstance(hist, list): errs.append('history: not a list'); hist = []
        if len(hist) > 6: errs.append('history: more than 6 turns')
        for i, t in enumerate(hist):
            if not isinstance(t, dict) or t.get('role') not in ('user', 'assistant') or set(t) != {'role', 'text'}: errs.append(f'history[{i}]: bad shape'); continue
            check_text(f'history[{i}]', t['text'], errs, cm, maxw=60, chunk_texts=alltexts)
        for a, b in zip(hist, hist[1:]):
            if isinstance(a, dict) and isinstance(b, dict) and a.get('role') == b.get('role'): errs.append('history: roles must alternate'); break
        if hist and hist[0].get('role') != 'user': errs.append('history: must start with user turn')
        ctx = s['context_scenario']
        if ctx in ('follow_up', 'slot_clarified') and not hist and not s['safety_leak']: errs.append('history: scenario needs a history')
        if ctx in ('self_contained',) and len(hist) > 2: errs.append('history: self_contained allows at most 2 turns')
        if ctx in ('no_policy', 'ambiguous_product') and len(hist) > 2: errs.append('history: too long for this scenario')
        if s['safety_leak']:
            if len(hist) > 3: errs.append('history: leaked records take 0 to 3 turns')
        rs = w.get('resolved_slots')
        want = set(f['context']['resolved_slot_keys'])
        if not isinstance(rs, dict): errs.append('resolved_slots: not an object')
        else:
            if set(rs) != want: errs.append(f'resolved_slots: keys {sorted(rs)} != {sorted(want)}')
            for k, v in rs.items():
                if not isinstance(v, str) or not v.strip(): errs.append(f'resolved_slots[{k}]: empty')
                elif any(c in v for c in BAD_CHARS): errs.append(f'resolved_slots[{k}]: forbidden char')
        # gold values of the same bundle must not be in history
        if all_written:
            for o in all_written:
                gv = o.get('gold_value') if o.get('kind') == 'qa' else None
                if gv and isinstance(gv, str) and len(gv) >= 4 and hist and any(gv.lower() in (t.get('text', '').lower()) for t in hist if isinstance(t, dict)):
                    errs.append('history: contains gold_value of the bundle')
        if set(w) - {'kind', 'query_id', 'query', 'history', 'resolved_slots'}: errs.append('unexpected keys: ' + str(sorted(set(w) - {'kind', 'query_id', 'query', 'history', 'resolved_slots'})))
        # numbers in assistant turns must be in history chunk (rule 8.3)
        hc = (job.get('history_chunk') or {}).get('text', '')
        for t in hist:
            if isinstance(t, dict) and t.get('role') == 'assistant':
                for num in re.findall(r'(?<![A-Za-z\d])\d+(?:[.,]\d+)?(?![A-Za-z])', t.get('text', '')):
                    if num not in hc: errs.append(f'history assistant turn: number {num} not in history chunk')
    else:
        q = w.get('question'); mods = set(f['noise_tags'])
        tele = 'telegraphic' in mods
        check_text('question', q, errs, False, maxw=40, minw=5, chunk_texts=alltexts)
        if tele and isinstance(q, str) and nw(q) != 5: errs.append(f'question: telegraphic QA uses exactly 5 words, has {nw(q)}')
        r = w.get('risposta'); fonte = w.get('fonte'); ab = f['question_type'] == 'absent'
        check_text('risposta', r, errs, False, chunk_texts=gold)
        if isinstance(r, str) and len(sentences(r)) > 3: errs.append('risposta: more than 3 sentences')
        if ab:
            if r != 'Non indicato nei documenti.': errs.append('absent: risposta must be exactly "Non indicato nei documenti."')
            if fonte is not None: errs.append('absent: fonte must be null')
            if w.get('gold_value') not in (None, ''): errs.append('absent: gold_value must be null')
        else:
            spans = fonte if isinstance(fonte, list) else [fonte]
            if f['question_type'] == 'multi_fact' and not isinstance(fonte, list): errs.append('multi_fact: fonte must be a list of spans')
            if f['question_type'] != 'multi_fact' and isinstance(fonte, list): errs.append('fonte must be one span')
            gn = norm(' '.join(gold))
            for sp in spans:
                if not isinstance(sp, str) or not sp.strip() or norm(sp) not in gn: errs.append(f'fonte: span not verbatim in gold chunks: {str(sp)[:60]!r}')
            gnums = set(re.findall(r'\d+(?:[.,]\d+)?', ' '.join(gold)))
            for num in re.findall(r'\d+(?:[.,]\d+)?', r or ''):
                if num not in gnums: errs.append(f'risposta: number {num} not in gold chunks')
            for k in ('gold_value',):
                if not isinstance(w.get(k), str) or not w[k].strip(): errs.append(f'{k}: required string')
            if w.get('gold_condition') is not None and not isinstance(w['gold_condition'], str): errs.append('gold_condition: string or null')
            if f['question_type'] == 'conditional' and not w.get('gold_condition'): errs.append('conditional: gold_condition required')
        if w.get('difficulty') not in ('easy', 'medium', 'hard'): errs.append('difficulty: easy|medium|hard')
        extra = set(w) - {'kind', 'qa_id', 'question', 'risposta', 'fonte', 'gold_value', 'gold_condition', 'difficulty'}
        if extra: errs.append(f'unexpected keys {sorted(extra)}')
    return errs

def validate_job(job, lines):
    """lines: parsed writer lines for this job. returns (per-record {id: errs}, skip_reason|None)"""
    by = {}; skip = None
    for w in lines:
        if w.get('kind') == 'skip': skip = w.get('reason', 'skip'); continue
        by[w.get('query_id') or w.get('qa_id')] = w
    out = {}
    recs = {(r['fixed'].get('query_id') or r['fixed'].get('qa_id')): r for r in job['records']}
    for rid, r in recs.items():
        w = by.get(rid)
        if w is None: out[rid] = ['missing record']; continue
        if w.get('kind') != r['kind']: out[rid] = ['wrong kind']; continue
        out[rid] = validate_record(job, r, w, [by[x] for x in by])
    for rid in by:
        if rid not in recs: out[rid] = ['id not in job']
    # pair rule
    pairs = {}
    for rid, r in recs.items():
        pid = r['fixed']['support']['pair_id'] if r['kind'] == 'router' else None
        if pid: pairs.setdefault(pid, []).append(rid)
    for pid, ids in pairs.items():
        if len(ids) == 2 and all(i in by and 'query' in by[i] and isinstance(by[i]['query'], str) for i in ids):
            d = pair_diff(by[ids[0]]['query'], by[ids[1]]['query'])
            if d > 8: [out[i].append(f'pair {pid}: queries differ by {d} words > 8') for i in ids]
            if d == 0: [out[i].append(f'pair {pid}: queries identical') for i in ids]
    return out, skip

def assemble(job, rec, w):
    f = rec['fixed']
    if rec['kind'] == 'router':
        s = dict(f['support']); s.update(bundle_id=f['bundle_id'], family=f['family'], split=f['split'])
        c = f['context']
        return {'query_id': f['query_id'], 'query': w['query'],
                'context': {'history': w['history'], 'selected_doc_id': c['selected_doc_id'], 'available_docs': c['available_docs'], 'resolved_slots': w['resolved_slots']},
                'labels': f['labels'], 'support': s}
    ab = f['question_type'] == 'absent'
    return {'qa_id': f['qa_id'], 'question': w['question'], 'evidence_record': [],
            'target': {'risposta': w['risposta'], 'fonte': w['fonte'], 'chunk_ids': [] if ab else list(f['gold_chunk_ids'])},
            'support': {'question_type': f['question_type'], 'expected_behavior': f['expected_behavior'], 'gold_chunk_ids': [] if ab else list(f['gold_chunk_ids']),
                        'gold_value': w.get('gold_value'), 'gold_condition': w.get('gold_condition'), 'retrieval_hit': None, 'gold_rank': None,
                        'difficulty': w['difficulty'], 'noise_tags': f['noise_tags'], 'bundle_id': f['bundle_id'], 'family': f['family'], 'split': f['split'],
                        'verified': False, 'generator': f['generator'], 'language': 'it', 'job_hints': {k: v for k, v in rec['hints'].items() if k in ('fact_index', 'topic', 'angle')}}}
