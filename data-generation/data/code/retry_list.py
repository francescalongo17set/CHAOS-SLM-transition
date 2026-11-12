"""Build retry lists for skipped jobs. Usage: python -I code/retry_list.py [--size 12]
Reads plan/skip_counts.json (run code/skip_stats.py first). Jobs still unwritten are split by the writer that should retry:
the OTHER model than the one that skipped (haiku skipped -> sonnet; sonnet skipped -> haiku, QA only; both -> sonnet).
Jobs whose gold chunk looks unwritable (short, fragment start, table-of-contents dots) or already skipped 2+ times go to
staging/bulk/retry/unlikely.txt, not to a writer. Writes staging/bulk/retry/<writer>_NNN.txt (lists) and retry/manifest.json.
Lists are separate from waves/, so bulk_waves.py (which counts skipped as done) is unaffected."""
import json, os, glob, re, collections
size = 12
S = json.load(open('plan/skip_counts.json'))
J = {}
for l in open('plan/jobs.jsonl'):
    j = json.loads(l); J[j['job_id']] = j
def weak(j):
    for c in j['chunks']:
        t = (c.get('text') or '').strip()
        if len(t) < 150 or t[:1].islower() or len(re.findall(r'\.{4,}', t)) >= 2: return True
    return False
out = collections.defaultdict(list); unl = []; man = {}
for jid, v in S.items():
    if v['now'] != 'skipped': continue
    j = J[jid]; w = set(v['writers'])
    if v['skips'] >= 2 or weak(j): unl.append(jid); man[jid] = 'unlikely'; continue
    who = 'sonnet' if 'haiku' in w else 'haiku'
    out[(who, j['scenario'])].append(jid); man[jid] = who
os.makedirs('staging/bulk/retry', exist_ok=True)
for f in glob.glob('staging/bulk/retry/*'): os.remove(f)
n = collections.Counter()
for who in ('sonnet', 'haiku'):
    ids = sorted(i for (w, sc), L in out.items() if w == who for i in L)
    ids.sort(key=lambda i: (J[i]['scenario'], i))
    for k in range(0, len(ids), size):
        open(f'staging/bulk/retry/{who}_{k // size + 1:03d}.txt', 'w').write('\n'.join(ids[k:k + size]) + '\n')
    n[who] = len(ids)
open('staging/bulk/retry/unlikely.txt', 'w').write('\n'.join(sorted(unl)) + '\n')
json.dump(man, open('staging/bulk/retry/manifest.json', 'w'), indent=1)
print('retry sonnet:', n['sonnet'], 'jobs | retry haiku:', n['haiku'], 'jobs | unlikely (weak chunk or 2+ skips):', len(unl))
