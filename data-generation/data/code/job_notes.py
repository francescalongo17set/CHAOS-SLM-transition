"""Writer-facing notes derived from the job (stage 6 revision 2): complexity requirement per feature and the client profile content.
Used by show_job.py and brief.py. Rules follow book s.4 (complexity table); comparisons use two chunks (one per product), so a complex comparison
is made with 2 or more fields or a criterion, never with 3 products."""
import json
PROFILES = {}
try:
    for l in open('seeds/client_profiles.jsonl'):
        p = json.loads(l); PROFILES[p['profile_id']] = p
except OSError:
    pass
NOTE = {
    ('product_policy_analysis', 'simple'): 'ONE fact or clause, one product, one chunk.',
    ('product_policy_analysis', 'complex'): 'combine 2+ chunks, or conditions and exceptions, or a trade-off, in the same request.',
    ('regulatory_consultation', 'simple'): 'ONE rule, one lookup, a single direct question.',
    ('regulatory_consultation', 'complex'): 'interpretation ACROSS SEVERAL rules: combine two conditions or obligations in one question (for example a date plus an exception, or two named rules that interact). A single-rule question is NOT complex.',
    ('client_drafting', 'simple'): 'one purpose, facts given, short message.',
    ('client_drafting', 'complex'): 'several facts, or a sensitive topic (claim refusal, complaint) or a negotiation.',
    ('ibip_screening', 'simple'): 'one criterion checked (for example horizon only).',
    ('ibip_screening', 'complex'): 'several criteria, or conflicting ones.',
}
def complexity_note(job, rec):
    f = rec['fixed']; l = f['labels']
    if l.get('scope_check') != 'in_scope' or not l.get('complexity'): return None
    feat, cx = l['feature'], l['complexity']
    if feat == 'comparison':
        ch = job.get('comparison_hint') or {}
        fields = ch.get('common_fields') or []
        if cx == 'complex':
            t = f"COMPLEX comparison = 2 products plus EITHER 2 or more fields (choose from {fields}) OR a criterion such as 'quale conviene' / 'meglio per un cliente che...'. Asking one field for two products is SIMPLE and wrong here."
        else:
            t = f"SIMPLE comparison = exactly 2 products and exactly 1 field ({ch.get('field')}), no criterion words (conviene, meglio, migliore)."
    else:
        t = NOTE.get((feat, cx))
        if not t: return None
        t = (cx.upper() + ' ' + feat + ' = ') + t
    if rec['hints'].get('pair_type') == 'complexity':
        t += ' This record is one half of a pair that differs in complexity: the two queries differ by at most 8 words, so the complex member adds its trigger in those words and the simple member leaves it out.'
    return t
def profile_note(rec):
    pid = rec['hints'].get('profile_id')
    if not pid: return None
    p = PROFILES.get(pid)
    return f"profile {pid}: {json.dumps({k: v for k, v in p.items() if k != 'profile_id'}, ensure_ascii=False)}" if p else f'profile {pid}: NOT FOUND'
