"""Plan bulk writing waves. Usage: python -I code/bulk_waves.py [--size 12] [--writer sonnet|haiku]
Pending = jobs not done/skipped in any job_status.json under staging/ or pilot/stg. Jobs are grouped by scenario so each agent sees similar jobs.
Writes staging/bulk/waves/<writer>_NNN.txt (job ids, one per line) and prints counts. Re-run any time: finished jobs drop out."""
import json, glob, os, sys, collections
size = int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 12
only = sys.argv[sys.argv.index('--writer') + 1] if '--writer' in sys.argv else None
done = set()
for f in glob.glob('staging/**/job_status.json', recursive=True) + glob.glob('pilot/**/job_status.json', recursive=True):
    for k, v in json.load(open(f)).items():
        if v.get('status') in ('done', 'skipped'): done.add(k)
A = json.load(open('plan/writer_assignment.json'))['assignment']
J = [json.loads(l) for l in open('plan/jobs.jsonl')]
pend = collections.defaultdict(list)
for j in J:
    if j['job_id'] not in done: pend[A[j['job_id']]].append(j)
os.makedirs('staging/bulk/waves', exist_ok=True)
for f in glob.glob('staging/bulk/waves/*.txt'): os.remove(f)
for w, js in pend.items():
    if only and w != only: continue
    js.sort(key=lambda j: (j['scenario'], j['job_id']))
    for i in range(0, len(js), size):
        open(f'staging/bulk/waves/{w}_{i // size + 1:03d}.txt', 'w').write('\n'.join(j['job_id'] for j in js[i:i + size]) + '\n')
    print(w, len(js), 'jobs ->', -(-len(js) // size), 'lists')
print('done jobs:', len(done))
