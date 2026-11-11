"""Pre-check of writer QA lines against retrieval: python -I code/qa_check.py batch.jsonl [models]  (default: bge, the frozen model).
Needs the shared server running (python -I code/retrieval_server.py); it never loads a model itself."""
import json, sys, os
os.environ["RETRIEVE_SERVER_ONLY"] = "1"
sys.path.insert(0, 'code')
from retrieve import retrieve
J = {}
for l in open('plan/jobs.jsonl'):
    j = json.loads(l); J[j['job_id']] = j
for l in open(sys.argv[1]):
    w = json.loads(l)
    if w.get('kind') != 'qa': continue
    rec = [r for r in J[w['job_id']]['records'] if r['fixed'].get('qa_id') == w['qa_id']][0]['fixed']
    if not rec['gold_chunk_ids']: continue
    doc = '_'.join(rec['gold_chunk_ids'][0].split('_')[:-2]); out = []
    for m in sys.argv[2].split(',') if len(sys.argv) > 2 else ('bge',):
        ids = [e['chunk_id'] for e in retrieve(w['question'], doc, 5, m)]
        out.append((m, [ids.index(g) + 1 if g in ids else None for g in rec['gold_chunk_ids']]))
    print(w['qa_id'], out)
