"""Stage 6: hit@5 of the two candidate embedding models on the pilot's answerable QA questions. Writes pilot/retrieval_compare.json"""
import json, sys
sys.path.insert(0, 'code')
from retrieve import retrieve
qa = [json.loads(l) for l in open('pilot/stg/accepted_qa.jsonl')]
res = {}
for m in ('e5', 'bge'):
    rows = []
    for r in qa:
        s = r['support']
        if s['expected_behavior'] != 'answer' or not s['gold_chunk_ids']: continue
        doc = '_'.join(s['gold_chunk_ids'][0].split('_')[:-2])
        ev = retrieve(r['question'], doc, 5, m); ids = [e['chunk_id'] for e in ev]
        ranks = [ids.index(g) + 1 if g in ids else None for g in s['gold_chunk_ids']]
        rows.append({'qa_id': r['qa_id'], 'type': s['question_type'], 'split': s['split'], 'ranks': ranks, 'all_in_top5': all(x for x in ranks), 'any_in_top5': any(x for x in ranks)})
    res[m] = {'n': len(rows), 'hit_all': sum(x['all_in_top5'] for x in rows) / len(rows), 'hit_any': sum(x['any_in_top5'] for x in rows) / len(rows), 'rows': rows}
    print(m, res[m]['n'], 'hit@5 all-gold', round(res[m]['hit_all'], 3), 'any-gold', round(res[m]['hit_any'], 3))
json.dump(res, open('pilot/retrieval_compare.json', 'w'), indent=1)
for a, b in zip(res['e5']['rows'], res['bge']['rows']): print(a['qa_id'], a['type'], 'e5', a['ranks'], 'bge', b['ranks'])
