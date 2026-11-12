"""Stage 9 (pilot use): build blind-pass inputs. Model input only, random ids, no labels/scenarios/source ids.
Usage: python -I code/verify_prepare.py <accepted_dir> <out_dir> <map_out.json> [--shards N] [--sample F]  (F = fraction of router and answerable QA records; absent QA always included)"""
import json, random, sys, os
random.seed(20261110)
src, out, mapf = sys.argv[1:4]; SAMPLE = float(sys.argv[sys.argv.index('--sample') + 1]) if '--sample' in sys.argv else 1.0; shards = int(sys.argv[sys.argv.index('--shards') + 1]) if '--shards' in sys.argv else 2
sys.path.insert(0, 'code')
from retrieve import retrieve
os.makedirs(out, exist_ok=True)
CH = {}
for l in open('chunks/chunks.jsonl'):
    c = json.loads(l); CH[c['chunk_id']] = c
mp = {}; R = []; Q = []
ids = set()
def rid(p):
    while True:
        x = p + '%05d' % random.randrange(100000)
        if x not in ids: ids.add(x); return x
for l in open(f'{src}/accepted_router.jsonl'):
    r = json.loads(l)
    if random.random() > SAMPLE: continue
    x = rid('r'); mp[x] = r['query_id']
    R.append({'id': x, 'query': r['query'], 'context': r['context']})
for l in open(f'{src}/accepted_qa.jsonl'):
    r = json.loads(l)
    if r['support']['expected_behavior'] == 'answer' and random.random() > SAMPLE: continue   # every absent QA is always checked
    x = rid('q'); mp[x] = r['qa_id']
    s = r['support']; gold = list(s['gold_chunk_ids'])
    doc = '_'.join((gold[0] if gold else r['target'].get('chunk_ids', ['x_x_x'])[0]).split('_')[:-2]) if gold else None
    if gold: ev = [CH[g] for g in gold]
    else: ev = []
    # pilot approximation: evidence = gold chunks + top retrieved others up to 5 (tests answering, not retrieval)
    if doc is None:  # absent: use the planner's section context via retrieval from the document the question names
        doc = {'zurich_salute': 'zurich_salute', 'generali': 'generali_immagina_adesso', 'impresa': 'zurich_impresa'}.get('zurich_salute')
        fam = s['family']; doc = fam.split('+')[0].replace('__heldout', '')
    for e in retrieve(r['question'], doc, 5, 'bge'):
        if len(ev) >= 5: break
        if e['chunk_id'] not in {c['chunk_id'] for c in ev}: ev.append(CH[e['chunk_id']])
    random.shuffle(ev)
    Q.append({'id': x, 'question': r['question'], 'evidence': [{'chunk_id': 'e%d' % i, 'section_path': c['section_path'], 'text': c['text']} for i, c in enumerate(ev)]})
    mp[x + ':evidence'] = [c['chunk_id'] for c in ev]
random.shuffle(R)
for i in range(shards):
    with open(f'{out}/router_input_{i+1}.jsonl', 'w') as f:
        for r in R[i::shards]: f.write(json.dumps(r, ensure_ascii=False) + '\n')
with open(f'{out}/qa_input.jsonl', 'w') as f:
    for q in Q: f.write(json.dumps(q, ensure_ascii=False) + '\n')
json.dump(mp, open(mapf, 'w'), indent=0)
print(len(R), 'router,', len(Q), 'qa ->', out)
