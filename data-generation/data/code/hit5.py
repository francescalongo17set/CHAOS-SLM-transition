"""Usage: python -I code/hit5.py <accepted_dir> [model]. hit@5 of answerable QA (all-gold and any-gold) with one model."""
import json, sys
sys.path.insert(0, 'code')
from retrieve import retrieve
d = sys.argv[1]; m = sys.argv[2] if len(sys.argv) > 2 else 'bge'
n = a = g = 0
for l in open(f'{d}/accepted_qa.jsonl'):
    r = json.loads(l); s = r['support']
    if s['expected_behavior'] != 'answer' or not s['gold_chunk_ids']: continue
    doc = '_'.join(s['gold_chunk_ids'][0].split('_')[:-2])
    top = [e['chunk_id'] for e in retrieve(r['question'], doc, 5, m)]
    ok = [c in top for c in s['gold_chunk_ids']]; n += 1; a += all(ok); g += any(ok)
    print(r['qa_id'], s['question_type'], ok)
print(m, 'n', n, 'all-gold', round(a / max(n, 1), 3), 'any-gold', round(g / max(n, 1), 3))
