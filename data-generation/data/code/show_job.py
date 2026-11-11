"""Print jobs in a compact readable form for the writer. Usage: python -I code/show_job.py job-000001 [...]  (or --file list.txt)"""
import json, sys
sys.path.insert(0, 'code')
from job_notes import complexity_note, profile_note
J = {}
for l in open('plan/jobs.jsonl'):
    j = json.loads(l); J[j['job_id']] = j
def show(jid, full_chunks=True):
    j = J[jid]
    print(f"##### {jid} scenario={j['scenario']} split={j['split']} pairs={j.get('pairs')}")
    for r in j['records']:
        f, h = r['fixed'], r['hints']
        if r['kind'] == 'qa':
            print(f"  QA {f['qa_id']} type={f['question_type']} tags={f['noise_tags']} gold={f['gold_chunk_ids']} hints={json.dumps(h,ensure_ascii=False)}")
        else:
            s, c, l = f['support'], f['context'], f['labels']
            print(f"  RT {f['query_id']} feat={l['feature']} cx={l.get('complexity')} miss={l.get('missing_info')} route={s['expected_route']} ctx={s['context_scenario']} dep={s['context_dependency']} style={s['query_style']} tags={s['noise_tags']}"
                  f" leak={s['safety_leak']}/{s['leak_type']}/{s['leak_difficulty']} pair={s['pair_id']}")
            print(f"     sel={c['selected_doc_id']} avail={c['available_docs']} resolved_keys={c['resolved_slot_keys']} slots={s['slot_status']}")
            print(f"     hints={json.dumps(h,ensure_ascii=False)}")
            for note in (complexity_note(j, r), profile_note(r)):
                if note: print('     >>', note)
        print(f"     seeds={json.dumps((r.get('seeds') or [])[:2],ensure_ascii=False)}")
    for c in j['chunks']:
        print(f"  CHUNK {c['chunk_id']} [{c['section_path']}]\n{c['text']}\n")
    hc = j.get('history_chunk')
    if hc: print(f"  HISTORY_CHUNK {hc['chunk_id']} [{hc.get('section_path')}]\n{hc['text']}\n")
    for hc in j.get('history_chunks') or []:
        print(f"  HISTORY_CHUNKS {json.dumps(hc,ensure_ascii=False)[:700]}")
    if 'comparison_hint' in j: print('  comparison_hint', j['comparison_hint'])
if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--file': a = open(a[1]).read().split()
    for x in a: show(x)
