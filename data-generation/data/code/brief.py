import json,sys
sys.path.insert(0,'code')
from job_notes import complexity_note, profile_note
J={}
for l in open('plan/jobs.jsonl'):
    j=json.loads(l);J[j['job_id']]=j
for jid in sys.argv[1:]:
    j=J[jid]; print('#####',jid,j['scenario'],j['split'])
    for r in j['records']:
        f,h=r['fixed'],r['hints']; s=f['support']; c=f['context']; l=f['labels']
        lk=h.get('leak') or {}
        print(f" {f['query_id']} {s['pair_id'] or ''}{('/'+str(h.get('pair_role'))) if s['pair_id'] else ''} {l['feature']}/{l.get('complexity')} miss={l.get('missing_info')} {s['expected_route']} ctx={s['context_scenario']} {s['query_style']} tags={s['noise_tags']} sel={c['selected_doc_id']} rk={c['resolved_slot_keys']} slots={s['slot_status']}")
        print(f"    topic={h.get('topic')} needs_date={h.get('needs_date')} slot_kind={h.get('slot_kind')} leak={lk.get('type')}/{lk.get('difficulty')}/app={lk.get('appended')}/fam={lk.get('phrasing_family')} lh={h.get('leak_history')} kind={h.get('kind')} sc={h.get('scenario')} extra={ {k:v for k,v in h.items() if k in ('quick','qtype','angle','intent','goal','profile','product','style_hint','near_miss','oos')} }")
        if 'profile' in h or 'client_profile' in h: print('    ',json.dumps({k:v for k,v in h.items() if 'prof' in k or 'goal' in k or 'product' in k},ensure_ascii=False))
        for note in (complexity_note(j, r), profile_note(r)):
            if note: print('     >>', note)
        print('    seeds:',json.dumps(r.get('seeds'),ensure_ascii=False)[:420])
