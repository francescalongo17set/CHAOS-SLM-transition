"""Stage 9 (used on the pilot): compare blind-pass output with recipe labels.
Usage: python -I code/verify.py <accepted_dir> <verify_dir> <map.json>
Writes <verify_dir>/disagreements.csv and prints agreement per field."""
import json, sys, csv, glob, collections
acc, vd, mapf = sys.argv[1:4]
mp = json.load(open(mapf)); inv = {v: k for k, v in mp.items() if not k.endswith(':evidence')}
out = {}
for f in glob.glob(f'{vd}/router_output_*.jsonl') + glob.glob(f'{vd}/qa_output.jsonl'):
    for l in open(f):
        if l.strip():
            r = json.loads(l); out[r['id']] = r
def norm(x): return (x or '').strip().lower().rstrip('.')
ag = collections.defaultdict(lambda: [0, 0]); rows = []
def chk(field, rid, a, b):
    ag[field][1] += 1
    if a == b: ag[field][0] += 1
    else: rows.append((rid, field, a, b))
for l in open(f'{acc}/accepted_router.jsonl'):
    r = json.loads(l); x = inv.get(r['query_id'])
    if x is None: continue   # not in the blind-pass sample
    o = out.get(x)
    if not o: ag['missing_output'][1] += 1; continue
    lb, sp = r['labels'], r['support']
    chk('scope_check', r['query_id'], lb['scope_check'], o.get('scope_check'))
    chk('feature', r['query_id'], lb['feature'], o.get('feature'))
    if lb['scope_check'] == 'in_scope':
        chk('complexity', r['query_id'], lb.get('complexity'), o.get('complexity'))
        os_ = o.get('slot_status') or {}
        for s, st in sp['slot_status'].items(): chk('slot:' + s if False else 'slot_status', r['query_id'] + ':' + s, st, os_.get(s))
    chk('route', r['query_id'], sp['expected_route'], o.get('route'))
for l in open(f'{acc}/accepted_qa.jsonl'):
    r = json.loads(l); x = inv.get(r['qa_id'])
    if x is None: continue
    o = out.get(x)
    if not o: ag['missing_output'][1] += 1; continue
    s = r['support']; absent = s['expected_behavior'] != 'answer'
    chk('qa_answerable', r['qa_id'], not absent, bool(o.get('answerable')))
    if not absent:
        gv = norm(s['gold_value']); ov = norm(o.get('value')) + ' ' + norm(o.get('answer'))
        chk('qa_value', r['qa_id'], True, gv in ov or all(t in ov for t in gv.split()))
        fo = r['target']['fonte']; fo = fo if isinstance(fo, list) else [fo]; sp_ = norm(o.get('span'))
        chk('qa_span', r['qa_id'], True, bool(sp_) and any(norm(f_) in sp_ or sp_ in norm(f_) for f_ in fo))
for k, (a, n) in sorted(ag.items()): print(f'{k:16s} {a}/{n} = {a/max(n,1):.3f}')
with open(f'{vd}/disagreements.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['id', 'field', 'recipe', 'blind']); w.writerows(rows)
print(len(rows), 'disagreements ->', f'{vd}/disagreements.csv')
