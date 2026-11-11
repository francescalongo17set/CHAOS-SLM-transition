"""Stage 7 trial: pick 100 non-pilot jobs stratified by scenario, assign writers and waves. Seed 20261110.
Writes staging/trial/jobs_<writer>_<wave>.txt (haiku_w1, sonnet_w1a, sonnet_w1b, sonnet_w2a, w2b, w2c)."""
import json, random, os
random.seed(20261110)
J = [json.loads(l) for l in open('plan/jobs.jsonl')]
A = json.load(open('plan/writer_assignment.json'))['assignment']
pilot = {l.strip() for l in open('pilot/pilot_jobs.txt') if l.strip()}
N = {'qa_single_value': 8, 'qa_conditional': 8, 'qa_multi_fact': 8, 'qa_absent': 6}
by = {}
for j in J:
    if j['job_id'] not in pilot: by.setdefault(j['scenario'], []).append(j['job_id'])
sel = {}
for s, ids in by.items():
    n = N.get(s, 3 if A[ids[0]] == 'haiku' else 5)
    sel[s] = random.sample(ids, min(n, len(ids)))
hk = [i for s in sel for i in sel[s] if A[i] == 'haiku']
sn = [i for s in sel for i in sel[s] if A[i] == 'sonnet']
random.shuffle(sn)
os.makedirs('staging/trial', exist_ok=True)
W = {'haiku_w1': hk, 'sonnet_w1a': sn[0:18], 'sonnet_w1b': sn[18:36], 'sonnet_w2a': sn[36:53], 'sonnet_w2b': sn[53:70], 'sonnet_w2c': sn[70:]}
for k, v in W.items(): open(f'staging/trial/jobs_{k}.txt', 'w').write('\n'.join(v) + '\n'); print(k, len(v))
