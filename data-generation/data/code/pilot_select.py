"""Stage 6: pick ~5% of jobs, stratified (>=3 per scenario, leak type, modifier, QA type). Seed 20261110. Output: pilot/pilot_jobs.txt"""
import json, random, collections
random.seed(20261110)
J = [json.loads(l) for l in open('plan/jobs.jsonl')]
def feats(j):
    f = {('scenario', j['scenario'])}
    for r in j['records']:
        if r['kind'] == 'qa': f.add(('qa_type', r['fixed']['question_type']))
        else:
            s = r['fixed']['support']
            if s['leak_type']: f.add(('leak', s['leak_type'] + '/' + str(s['leak_difficulty'])))
            for m in s['noise_tags']: f.add(('mod', m))
            f.add(('ctx', s['context_scenario'])); f.add(('style', s['query_style']))
    return f
need = collections.Counter(); F = {j['job_id']: feats(j) for j in J}
for f in F.values():
    for x in f: need[x] += 1
# cost: records in job (keep jobs small)
chosen, have = [], collections.Counter()
target = {x: (3 if x[0] != 'style' else 5) for x in need}
pool = J[:]; random.shuffle(pool)
def gain(j): return sum(1 for x in F[j['job_id']] if have[x] < target[x]) / (1 + 0.1*len(j['records']))
while True:
    pool.sort(key=gain, reverse=True)
    b = pool[0]
    if gain(b) <= 0 or len(chosen) >= 140: break
    chosen.append(b['job_id']); pool.pop(0)
    for x in F[b['job_id']]: have[x] += 1
open('pilot/pilot_jobs.txt', 'w').write('\n'.join(sorted(chosen)) + '\n')
nrec = sum(len(j['records']) for j in J if j['job_id'] in set(chosen))
print(len(chosen), 'jobs', nrec, 'records', 'uncovered', [x for x in need if have[x] < min(target[x], need[x])])
print(collections.Counter(j['scenario'] for j in J if j['job_id'] in set(chosen)))
