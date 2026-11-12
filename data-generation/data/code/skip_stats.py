"""Count how many times each job was skipped. Usage: python -I code/skip_stats.py
Scans every job_status.json under staging/ and pilot/ (one folder = one attempt round; a consolidated folder
counts once per job). Writer = haiku for staging/bulk/h_* and r_h_* (retry), sonnet otherwise (incl. r_s_*). Writes plan/skip_counts.json
({job_id: {skips, folders, writers, last_reason, now}}) where now = done|skipped|pending (by latest status of
any folder: done wins). Also writes plan/dropped_jobs.json (owner rule: skipped twice = dropped). Re-run any time; it is read-only except for that file.
Caveat: history before the 12 Nov evening rounds is consolidated (final_b2..b4), so earlier repeat skips may be undercounted."""
import json, glob, os, collections
sk = collections.defaultdict(list); done = set()
for f in sorted(glob.glob('staging/**/job_status.json', recursive=True) + glob.glob('pilot/**/job_status.json', recursive=True)):
    folder = os.path.basename(os.path.dirname(f)); w = 'haiku' if folder.startswith(('h_', 'r_h_')) else 'sonnet'
    for j, v in json.load(open(f)).items():
        if v.get('status') == 'done': done.add(j)
        elif v.get('status') == 'skipped': sk[j].append((folder, w, v.get('reason', '')))
J = [json.loads(l)['job_id'] for l in open('plan/jobs.jsonl')]
out = {}
for j, L in sk.items():
    out[j] = {'skips': len(L), 'folders': [x[0] for x in L], 'writers': [x[1] for x in L], 'last_reason': L[-1][2],
              'now': 'done' if j in done else 'skipped'}
os.makedirs('plan', exist_ok=True); json.dump(out, open('plan/skip_counts.json', 'w'), indent=1)
drop = sorted(j for j, v in out.items() if v['skips'] >= 2 and v['now'] == 'skipped')
json.dump({'rule': 'owner 12 Nov 2026: a job skipped twice is dropped (never retried, no replacement)', 'jobs': drop}, open('plan/dropped_jobs.json', 'w'), indent=1)
print('dropped (skipped twice, still unwritten):', len(drop), '-> plan/dropped_jobs.json')
c = collections.Counter(v['skips'] for v in out.values())
print('jobs skipped at least once:', len(out), '| distribution (times skipped: jobs):', dict(sorted(c.items())))
print('later written (done):', sum(v['now'] == 'done' for v in out.values()), '| still unwritten:', sum(v['now'] == 'skipped' for v in out.values()))
bw = collections.Counter(w for v in out.values() for w in v['writers']); print('skips by writer:', dict(bw))
rep = sorted((j for j, v in out.items() if v['skips'] >= 2 and v['now'] == 'skipped'), key=lambda j: -out[j]['skips'])
print('skipped 2+ times and still unwritten:', len(rep), rep[:15])
