"""Replace the topic of planned absent-QA jobs whose topic turned out not to be absent (found by the blind pass).
Usage: python -I code/replace_absent.py   (idempotent: a round is applied only to jobs still holding that round's old topic)
Rounds 1-2 (11 Nov) Generali only; round 3 (12 Nov) all families. Only hints change (topic, terms, angle = first free 1..5, replaces_topic); ids, labels, split and context chunks stay. Old job versions are appended to the archive."""
import json, hashlib, csv, os
ROUNDS = [  # (old topic, {job_id: new topic}, reason)
    ('rateazione e frazionamento del premio', {'job-000833': 'arbitrato', 'job-000834': 'coassicurazione', 'job-000835': 'periodo di osservazione', 'job-000836': 'interessi di mora'},
     'document lists instalments (rate mensili, trimestrali, semestrali); found by blind pass on bulk batch 1'),
    ('periodo di osservazione', {'job-000835': 'duplicato della polizza'},
     "document has a 'Termine di aspettativa' (waiting period) for natural events; found by blind pass on the replacements"),
    # Round 3 (12 Nov 2026): blind pass on 272 absent QA of bulk batch 3 (verify/absent3) + qa-000260
    ('affitti brevi e locazione turistica', {'job-000748': 'piscina e impianti sportivi'}, 'blind pass absent3: borderline answerable'),
    ('lavori di ristrutturazione e appaltatori', {'job-000804': 'domotica e dispositivi smart'}, 'blind pass absent3: answerable'),
    ('arbitrato', {'job-000751': 'trasferimento della polizza a un nuovo titolare'}, 'blind pass absent3: borderline answerable'),
    ('periodo di osservazione', {'job-000813': 'trasferimento della polizza a un nuovo titolare', 'job-000814': 'risoluzione per decesso del contraente', 'job-000815': 'risoluzione per decesso del contraente', 'job-000299': 'bonus e sconti per assenza di sinistri'}, 'blind pass absent3: waiting period exists under another name'),
    ('riattivazione della polizza', {'job-000837': 'polizza in valuta estera', 'job-000839': 'polizza collettiva o convenzione aziendale'}, 'blind pass absent3: answerable'),
    ('rimborso del premio non goduto', {'job-000843': 'premio minimo', 'job-000844': 'lingua del contratto', 'job-001931': 'risoluzione per decesso del contraente'}, 'blind pass absent3: answerable'),
    ('giorni di tolleranza per il pagamento', {'job-000285': 'risoluzione per decesso del contraente', 'job-000286': 'premio minimo'}, 'blind pass absent3: answerable'),
    ('cambio del piano o della forma di copertura', {'job-000260': 'coassicurazione'}, 'blind pass bulk2: document allows written policy changes'),
]
cand = {(r['doc_id'], r['topic']): r for r in csv.DictReader(open('catalogue/absent_candidates.csv'))}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
import collections
TAKEN = collections.defaultdict(set)
for x in open('plan/jobs.jsonl'):
    x = json.loads(x); r0 = x['records'][0]
    TAKEN[(r0['fixed']['family'], r0['hints'].get('topic'))].add(r0['hints'].get('angle'))
before = sha('plan/jobs.jsonl'); out = []; arch = []; applied = []
for l in open('plan/jobs.jsonl'):
    j = json.loads(l)
    for old, m, why in ROUNDS:
        if j['job_id'] in m and j['records'][0]['hints']['topic'] == old:
            h = j['records'][0]['hints']; arch.append(l); t = cand[(j['records'][0]['fixed']['family'], m[j['job_id']])]
            assert t['expected_section'] == h['expected_section'] and t['split'] == j['split'] and t['usable'] == 'true' and t['hits'] == '0'
            fam = j['records'][0]['fixed']['family']; ang = next(a for a in range(1, 6) if a not in TAKEN[(fam, t['topic'])]); TAKEN[(fam, t['topic'])].add(ang)
            h.update({'topic': t['topic'], 'terms': t['terms_searched'], 'angle': ang, 'replaces_topic': old}); applied.append((j['job_id'], old, t['topic']))
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
