"""Replace the topic of planned absent-QA jobs whose topic turned out not to be absent (found by the blind pass).
Usage: python -I code/replace_absent.py   (idempotent: a round is applied only to jobs still holding that round's old topic)
Only hints change (topic, terms, angle 5, replaces_topic); ids, labels, split and context chunks stay. Old job versions are appended to the archive."""
import json, hashlib, csv, os
ROUNDS = [  # (old topic, {job_id: new topic}, reason)
    ('rateazione e frazionamento del premio', {'job-000833': 'arbitrato', 'job-000834': 'coassicurazione', 'job-000835': 'periodo di osservazione', 'job-000836': 'interessi di mora'},
     'document lists instalments (rate mensili, trimestrali, semestrali); found by blind pass on bulk batch 1'),
    ('periodo di osservazione', {'job-000835': 'duplicato della polizza'},
     "document has a 'Termine di aspettativa' (waiting period) for natural events; found by blind pass on the replacements"),
]
cand = {r['topic']: r for r in csv.DictReader(open('catalogue/absent_candidates.csv')) if r['doc_id'] == 'generali_immagina_adesso'}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
before = sha('plan/jobs.jsonl'); out = []; arch = []; applied = []
for l in open('plan/jobs.jsonl'):
    j = json.loads(l)
    for old, m, why in ROUNDS:
        if j['job_id'] in m and j['records'][0]['hints']['topic'] == old:
            h = j['records'][0]['hints']; arch.append(l); t = cand[m[j['job_id']]]
            assert t['expected_section'] == h['expected_section'] and t['split'] == j['split'] and t['usable'] == 'true' and t['hits'] == '0'
            h.update({'topic': t['topic'], 'terms': t['terms_searched'], 'angle': 5, 'replaces_topic': old}); applied.append((j['job_id'], old, t['topic']))
            l = json.dumps(j, ensure_ascii=False) + '\n'
    out.append(l)
if not applied: print('nothing to apply'); raise SystemExit
open('plan/replaced_jobs_archive.jsonl', 'a').writelines(arch)
open('plan/jobs.jsonl.tmp', 'w').writelines(out); os.replace('plan/jobs.jsonl.tmp', 'plan/jobs.jsonl'); after = sha('plan/jobs.jsonl')
with open('plan/replacements.md', 'a') as f:
    f.write(f"\n## Applied {len(applied)} replacement(s)\n" + ''.join(f"- {a}: '{b}' -> '{c}'\n" for a, b, c in applied))
    for old, m, why in ROUNDS: f.write(f"- Reason for '{old}': {why}\n")
    f.write(f"jobs.jsonl sha256 before: {before}\njobs.jsonl sha256 after:  {after}\nRe-running plan.py does not reproduce jobs.jsonl; re-apply this script afterwards. Each new topic: synonym search of all Generali chunks, 0 real hits; angle 5 (cap 5 kept).\n")
print('applied', applied, before[:12], '->', after[:12])
