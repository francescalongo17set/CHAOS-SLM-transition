"""Usage: python -I code/write_batch.py <batch.jsonl> [--dir pilot] [--writer <model id>]
Reads writer lines, caches them, validates per job, appends accepted (assembled) records to <dir>/accepted_{router,qa}.jsonl, rejected to <dir>/rejected.jsonl.
Bundles (qa_*, pairs_*, router_only_*) are accepted all-or-nothing; other no-document jobs record by record. Job status in <dir>/job_status.json."""
import json, sys, os, time, collections
if '--no-check' not in sys.argv: os.environ['RETRIEVE_SERVER_ONLY'] = '1'
sys.path.insert(0, 'code')
from validate import validate_job, assemble, VALIDATOR_VERSION
a = sys.argv[1:]; D = 'staging'
if '--dir' in a: D = a[a.index('--dir') + 1]
WRITER = a[a.index('--writer') + 1] if '--writer' in a else None   # overrides the generator field (use for non-default writer models)
batch = a[0]; os.makedirs(D, exist_ok=True); os.makedirs('cache', exist_ok=True)
J = {}
for l in open('plan/jobs.jsonl'):
    j = json.loads(l); J[j['job_id']] = j
st_path = f'{D}/job_status.json'
st = json.load(open(st_path)) if os.path.exists(st_path) else {}
lines = [json.loads(l) for l in open(batch) if l.strip()]
if '--replace' in a:   # regenerate: drop previously accepted records with the same ids, then treat as new
    ids = {(w.get('query_id') or w.get('qa_id')) for w in lines}
    for kind in ('router', 'qa'):
        fp = f'{D}/accepted_{kind}.jsonl'
        if os.path.exists(fp):
            keep = [l for l in open(fp) if (json.loads(l).get('query_id') or json.loads(l).get('qa_id')) not in ids]
            open(fp, 'w').writelines(keep)
    for w in lines:
        s0 = st.get(w['job_id'])
        if s0: s0['accepted'] = [x for x in s0['accepted'] if x not in ids]
# job_id is carried in every line
bj = collections.defaultdict(list)
for w in lines: bj[w['job_id']].append(w)
with open('cache/writes.jsonl', 'a') as c: c.write(json.dumps({'t': time.time(), 'batch': batch, 'dir': D, 'lines': lines}, ensure_ascii=False) + '\n')
tot = collections.Counter()
for jid, ws in bj.items():
    job = J[jid]; ws = [{k: v for k, v in w.items() if k != 'job_id'} for w in ws]
    errs, skip = validate_job(job, ws)
    by = {(w.get('query_id') or w.get('qa_id')): w for w in ws if w.get('kind') != 'skip'}
    bundle = job['scenario'].startswith(('qa_', 'pairs_', 'router_only')) 
    s = st.setdefault(jid, {'accepted': [], 'attempts': 0, 'status': 'pending'}); s['attempts'] += 1
    if skip and not by:
        s['status'] = 'skipped'; s['reason'] = skip; tot['skipped'] += 1; continue
    recs = {(r['fixed'].get('query_id') or r['fixed'].get('qa_id')): r for r in job['records']}
    warns = {k: [x for x in v if x.startswith('warn:')] for k, v in errs.items()}
    for k, w_ in warns.items():
        if w_: open(f'{D}/warnings.jsonl', 'a').write(json.dumps({'job_id': jid, 'id': k, 'warnings': w_, 'written': by.get(k)}, ensure_ascii=False) + '\n')
    errs = {k: [x for x in v if not x.startswith('warn:')] for k, v in errs.items()}
    if '--no-check' not in a:   # built-in retrieval pre-check (bge via shared server): answerable QA need a gold chunk in the top 5; multi_fact = any gold (G3 rule), all-gold logged
        from retrieve import retrieve
        for k, r in recs.items():
            g = r['fixed'].get('gold_chunk_ids') if r['kind'] == 'qa' else None
            if not g or k not in by or errs.get(k): continue
            top = [e['chunk_id'] for e in retrieve(by[k]['question'], '_'.join(g[0].split('_')[:-2]), 5, 'bge')]
            rk = [top.index(x) + 1 if x in top else None for x in g]
            open(f'{D}/retrieval.jsonl', 'a').write(json.dumps({'job_id': jid, 'qa_id': k, 'attempt': s['attempts'], 'ranks': rk, 'any': any(rk), 'all': all(rk)}) + '\n')
            if not any(rk): errs[k] = [f'retrieval: no gold chunk in bge top 5 (ranks {rk}); reword with more distinctive terms (max 3 tries, then skip)']
    bad = {k: v for k, v in errs.items() if v}
    ok_ids = [k for k in recs if k in by and k not in bad] if not bundle else (list(recs) if not bad else [])
    ok_ids = [k for k in ok_ids if k not in s['accepted']]
    for k in ok_ids:
        r = recs[k]; rec = assemble(job, r, by[k])
        if WRITER: rec['support']['generator'] = WRITER
        open(f'{D}/accepted_{r["kind"]}.jsonl', 'a').write(json.dumps(rec, ensure_ascii=False) + '\n'); s['accepted'].append(k)
    for k, e in bad.items():
        if k in s['accepted']: continue
        open(f'{D}/rejected.jsonl', 'a').write(json.dumps({'job_id': jid, 'id': k, 'attempt': s['attempts'], 'errors': e, 'written': by.get(k)}, ensure_ascii=False) + '\n')
    s['status'] = 'done' if len(s['accepted']) == len(recs) else 'pending'
    s['last_errors'] = {k: v for k, v in bad.items() if k not in s['accepted']}
    tot['jobs_done' if s['status'] == 'done' else 'jobs_pending'] += 1; tot['rec_ok'] += len(ok_ids); tot['rec_bad'] += len(bad)
json.dump(st, open(st_path, 'w'), indent=1)
print(dict(tot))
for jid in bj:
    for k, e in st[jid].get('last_errors', {}).items(): print(' REJECT', jid, k, '|', '; '.join(e)[:300])
