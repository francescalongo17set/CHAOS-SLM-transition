"""Stage 8 step 5: replacement jobs for the records still missing after postprocess.py (book stage 8, step 5).

Run from data/ after postprocess.py:  python -I code/make_replacements.py [--dry-run]
For every plan record that is not in post/router.jsonl or post/qa.jsonl it builds a NEW job (fresh job/bundle/record ids, never the skipped job again):
  qa_* bundles (QA record missing)  full clone, new gold chunk(s) of the same document/pool, not used by any skipped or dropped job
                                    (only-router-companion-missing bundles and qa_absent are not replaced)
  router_only comparison            clone with NEW chunk pair (common field), available_docs corrected to hold both compared docs (planner defect G3)
  router_only lookup                clone with ONE new chunk, no comparison_hint, no second product (planner defect: lookup jobs carried a second chunk)
  all other no-document jobs        clone of the missing records only (pairs are cloned whole with a new pair id)
Appends to plan/jobs.jsonl and plan/writer_assignment.json (haiku). Backups: plan/jobs.jsonl.bak_round4, plan/writer_assignment.json.bak_round4.
Writes plan/replacements_round4.json (new job -> old job, reason) and prints counts. Seed 20261110."""
import json, sys, copy, random, collections, shutil, os, re

DRY = '--dry-run' in sys.argv
rng = random.Random(20261110)
J = [json.loads(l) for l in open('plan/jobs.jsonl')]
if any(j['job_id'] >= 'job-002065' for j in J):
    sys.exit('replacement jobs already present (job ids above 002064): restore plan/jobs.jsonl.bak_round4 to rebuild')
chunks = {}
for l in open('chunks/chunks.jsonl', encoding='utf-8'):
    c = json.loads(l); chunks[c['chunk_id']] = c
cat = {}
for l in open('catalogue/chunk_catalogue.jsonl', encoding='utf-8'):
    c = json.loads(l); cat[c['chunk_id']] = c
got_r = {json.loads(l)['query_id'] for l in open('post/router.jsonl')}
got_q = {json.loads(l)['qa_id'] for l in open('post/qa.jsonl')}
sup = set(json.load(open('plan/superseded_qa.json'))['dropped_no_replacement'])
sk = json.load(open('plan/skip_counts.json'))
dropped = set(json.load(open('plan/dropped_jobs.json'))['jobs'])
unlikely = set(l.strip() for l in open('staging/bulk/retry/unlikely.txt') if l.strip()) if os.path.exists('staging/bulk/retry/unlikely.txt') else set()
bad_jobs = dropped | unlikely | {k for k, v in sk.items() if v.get('now') != 'done'}
JB = {j['job_id']: j for j in J}

def chunk_ids_of(j):
    s = set()
    for r in j['records']:
        f = r['fixed']
        s |= set(f.get('gold_chunk_ids') or []) | set((f.get('support') or {}).get('source_chunk_ids') or [])
    return s
avoid = set()
for jid in bad_jobs:
    if jid in JB: avoid |= chunk_ids_of(JB[jid])
use = collections.Counter()
for j in J:
    for cid in chunk_ids_of(j): use[cid] += 1

def weak(cid):
    c = chunks[cid]; t = c['text']
    return c['n_chars'] < 300 or '....' in t or t[:1].islower()

def pick(doc, pool, usable=None, field=None, section=None, exclude=(), n=1):
    cand = [cid for cid, c in cat.items() if c['doc_id'] == doc and c['pool'] == pool and cid not in avoid and cid not in exclude
            and not weak(cid) and (usable is None or usable in c['usable_for']) and (field is None or field in c['fields_found'])
            and (section is None or c['top_section'] == section) and use[cid] < 6]
    rng.shuffle(cand)
    cand.sort(key=lambda cid: use[cid])
    return cand[:n]

def cdict(cid):
    return {k: chunks[cid][k] for k in ('branch', 'chunk_id', 'doc_id', 'insurer', 'page', 'product', 'section_path', 'text')}

POOL = {'train': 'train_pool', 'validation': 'validation_pool', 'test': 'test_pool'}
nxt = {'job': max(int(j['job_id'][4:]) for j in J) + 1, 'b': max(int(j['bundle_id'][2:]) for j in J) + 1,
       'qa': max(int(r['fixed']['qa_id'][3:]) for j in J for r in j['records'] if r['kind'] == 'qa') + 1,
       'orc': max(int(r['fixed']['query_id'][4:]) for j in J for r in j['records'] if r['kind'] == 'router') + 1,
       'pair': max([int(r['fixed']['support']['pair_id'][5:]) for j in J for r in j['records'] if r['kind'] == 'router' and r['fixed']['support'].get('pair_id')] + [0]) + 1}

def newid(k, fmt):
    v = nxt[k]; nxt[k] += 1; return fmt % v

def reuse_all(new, old_chunk_ids, new_chunk_ids):
    """swap chunk ids inside records and job chunks"""
    mp = dict(zip(old_chunk_ids, new_chunk_ids))
    for r in new['records']:
        f = r['fixed']
        if 'gold_chunk_ids' in f: f['gold_chunk_ids'] = [mp.get(c, c) for c in f['gold_chunk_ids']]
        if f.get('support') and f['support'].get('source_chunk_ids'): f['support']['source_chunk_ids'] = [mp.get(c, c) for c in f['support']['source_chunk_ids']]

def finish(new, old, reason, only=None):
    nj = newid('job', 'job-%06d'); nb = newid('b', 'b-%06d')
    new['job_id'] = nj; new['bundle_id'] = nb
    pm = {}
    recs = [r for r in new['records'] if only is None or (r['fixed'].get('qa_id') or r['fixed'].get('query_id')) in only]
    new['records'] = recs
    for r in recs:
        f = r['fixed']; f['bundle_id'] = nb
        if r['kind'] == 'qa': f['qa_id'] = newid('qa', 'qa-%06d')
        else:
            f['query_id'] = newid('orc', 'orc-%06d')
            p = f['support'].get('pair_id')
            if p:
                pm.setdefault(p, newid('pair', 'pair-%04d')); f['support']['pair_id'] = pm[p]
    return nj

out, log = [], []
cnt = collections.Counter(); lost = collections.Counter()

for j in J:
    miss = [r for r in j['records'] if (r['fixed'].get('query_id') or r['fixed']['qa_id']) not in (got_r if r['kind'] == 'router' else got_q)
            and (r['fixed'].get('qa_id') or '') not in sup]
    if not miss: continue
    sc, split = j['scenario'], j['split']
    mids = {(r['fixed'].get('query_id') or r['fixed']['qa_id']) for r in miss}
    if sc.startswith('qa_'):
        if sc == 'qa_absent' or not any(r['kind'] == 'qa' for r in miss):
            lost[sc + (' (router companion only)' if sc != 'qa_absent' else '')] += len(miss); continue
        new = copy.deepcopy(j); old_ids = list(j['records'][0]['fixed'].get('gold_chunk_ids') or [])
        qrec = next(r for r in j['records'] if r['kind'] == 'qa'); qt = qrec['fixed']['question_type']
        old_ids = qrec['fixed']['gold_chunk_ids']; doc = qrec['fixed']['family'].split('__')[0]
        k = len(old_ids)
        first = pick(doc, POOL[split], usable=qt)
        if not first: lost[sc + ' (no chunk)'] += len(miss); continue
        sel = first
        if k > 1:
            sibs = pick(doc, POOL[split], usable='multi_fact', section=cat[first[0]]['top_section'], exclude=first, n=k - 1)
            if len(sibs) < k - 1: lost[sc + ' (no siblings)'] += len(miss); continue
            sel = first + sibs
        for c in sel: use[c] += 1
        reuse_all(new, old_ids, sel)
        new['chunks'] = [cdict(c) for c in sel]
        hc = new.get('history_chunk')
        if hc and hc['chunk_id'] in sel:
            alt = pick(doc, POOL[split], exclude=sel)
            new['history_chunk'] = cdict(alt[0]) if alt else None
        nj = finish(new, j, 'qa_missing')
        out.append(new); log.append({'new': nj, 'old': j['job_id'], 'scenario': sc, 'split': split, 'records': len(new['records'])}); cnt[sc] += len(new['records'])
    elif sc in ('router_only_agentic_comparison', 'router_only_lightweight_simple_comparison'):
        new = copy.deepcopy(j); r = new['records'][0]; f = r['fixed']
        fam = f['family']; da, db = [x.split('__')[0] for x in fam.split('+')]
        fld = j.get('comparison_hint', {}).get('field')
        A = pick(da, POOL[split], field=fld); B = pick(db, POOL[split], field=fld)
        if not A or not B:
            A = pick(da, POOL[split]); B = pick(db, POOL[split]); fld = None
        if not A or not B: lost[sc + ' (no chunks)'] += 1; continue
        A, B = A[0], B[0]; use[A] += 1; use[B] += 1
        common = sorted(set(cat[A]['fields_found']) & set(cat[B]['fields_found']))
        if not common: lost[sc + ' (no common field)'] += 1; continue
        if fld not in common: fld = common[0]
        new['chunks'] = [cdict(A), cdict(B)]
        new['comparison_hint'] = {'field': fld, 'common_fields': common}
        for rr in new['records']:
            ff = rr['fixed']; ff['support']['source_chunk_ids'] = [A, B]
            ctx = ff['context']; ctx['available_docs'] = sorted(set(ctx['available_docs']) | {da, db} | {'italiana_ri_plus'})
            if ctx.get('selected_doc_id') and ctx['selected_doc_id'] not in (da, db): ctx['selected_doc_id'] = da
        hc = new.get('history_chunk')
        if hc and hc['chunk_id'] in (A, B): new['history_chunk'] = None
        nj = finish(new, j, 'comparison_available_docs_fixed', only=mids)
        out.append(new); log.append({'new': nj, 'old': j['job_id'], 'scenario': sc, 'split': split, 'records': len(new['records'])}); cnt[sc] += len(new['records'])
    elif sc == 'router_only_lightweight_product_lookup':
        # lookup jobs are pairs: a lookup record (one product) and a comparison record (two products). Keep both shapes, fix available_docs.
        new = copy.deepcopy(j)
        pa = next((r for r in new['records'] if r['fixed']['labels']['feature'] != 'comparison'), new['records'][0])
        cm = next((r for r in new['records'] if r['fixed']['labels']['feature'] == 'comparison'), None)
        da = chunks[pa['fixed']['support']['source_chunk_ids'][0]]['doc_id']
        db = None
        if cm is not None:
            docs = {chunks[c]['doc_id'] for c in cm['fixed']['support']['source_chunk_ids']} - {da}
            db = sorted(docs)[0] if docs else None
            if db is None:
                db = 'zurich_salute' if da != 'zurich_salute' else 'generali_immagina_adesso'
            if split == 'validation' and db == da: db = None
        A = pick(da, POOL[split], usable='single_value')
        if not A: lost[sc + ' (no chunk)'] += 1; continue
        B = []
        if cm is not None:
            for a_ in A[:6]:
                for fld_ in cat[a_]['fields_found']:
                    B = pick(db, POOL[split], field=fld_)
                    if B: A = [a_]; break
                if B: break
            if not B: lost[sc + ' (no second chunk)'] += len(miss); continue
        A = A[0]; use[A] += 1
        if B: use[B[0]] += 1
        common = sorted(set(cat[A]['fields_found']) & set(cat[B[0]]['fields_found'])) if B else []
        new['chunks'] = [cdict(A)] + ([cdict(B[0])] if B else [])
        if B: new['comparison_hint'] = {'field': common[0], 'common_fields': common}
        else: new.pop('comparison_hint', None)
        new.pop('pa_chunk_id', None)
        for rr in new['records']:
            ff = rr['fixed']; is_cmp = ff['labels']['feature'] == 'comparison'
            ff['support']['source_chunk_ids'] = [A] + ([B[0]] if (is_cmp and B) else [])
            ctx = ff['context']
            ctx['available_docs'] = sorted(set(ctx['available_docs']) | {da} | ({db} if (is_cmp and B) else set()))
            if ctx.get('selected_doc_id') and ctx['selected_doc_id'] not in ({da, db} if is_cmp else {da}): ctx['selected_doc_id'] = da
            ff['family'] = da + ('__heldout' if split == 'validation' else '') if not is_cmp else '+'.join(sorted([da, db or da]))
        hc = new.get('history_chunk')
        if hc and hc['chunk_id'] in ([A] + B): new['history_chunk'] = None
        nj = finish(new, j, 'lookup_pair_fixed', only=mids)
        out.append(new); log.append({'new': nj, 'old': j['job_id'], 'scenario': sc, 'split': split, 'records': len(new['records'])}); cnt[sc] += len(new['records'])
    else:
        new = copy.deepcopy(j)
        nj = finish(new, j, 'clone_missing_records', only=mids)
        out.append(new); log.append({'new': nj, 'old': j['job_id'], 'scenario': sc, 'split': split, 'records': len(new['records'])}); cnt[sc] += len(new['records'])

print('new jobs:', len(out), 'records:', sum(cnt.values()))
for k, v in cnt.most_common(): print(' ', k, v)
print('not replaced:', dict(lost), sum(lost.values()))
if DRY: sys.exit()
shutil.copy('plan/jobs.jsonl', 'plan/jobs.jsonl.bak_round4'); shutil.copy('plan/writer_assignment.json', 'plan/writer_assignment.json.bak_round4')
with open('plan/jobs.jsonl', 'a', encoding='utf-8') as fh:
    for n in out: fh.write(json.dumps(n, ensure_ascii=False) + '\n')
W = json.load(open('plan/writer_assignment.json'))
for n in out: W['assignment'][n['job_id']] = 'haiku'
json.dump(W, open('plan/writer_assignment.json', 'w'), indent=1)
json.dump(log, open('plan/replacements_round4.json', 'w'), indent=1)
print('appended', len(out), 'jobs (haiku)')
