# Task: label Italian insurance-assistant requests (blind check)

You see only the model input. You cannot see any recipe, plan or labels. Decide from the text alone.

## Router records (file router_input_N.jsonl; fields id, query, context)
context = history (list of turns), selected_doc_id, available_docs, resolved_slots. Slot values may be resolved from history, selected_doc_id or resolved_slots.
Output one JSON line per record:
{"id":..., "scope_check":"in_scope|out_of_scope|quick_reply", "feature":"product_policy_analysis|comparison|regulatory_consultation|client_drafting|ibip_screening|none", "complexity":"simple|complex|null", "slot_status":{"<slot>":"present|missing|ambiguous"}, "route":"quick_reply|refuse|clarification|agentic|lightweight"}

Features and required slots:
- product_policy_analysis: insurer, product, field, coverage
- comparison: insurer, product, field, coverage (filled only when every compared product is identified)
- regulatory_consultation: topic; date_reference. date_reference is a required slot ONLY when the correct answer would differ depending on a date or period (e.g. which rule applied at a given time, deadlines counted from an event, a change of regime). If the request already states the date/period, report it as present. If the answer does not depend on a date, do NOT list date_reference at all. A vague 'di recente' or 'una volta' where a date matters is ambiguous; no date given where it matters is missing.
- client_drafting: product, client_profile, message_goal
- ibip_screening: product, client_profile
feature none = out_of_scope or quick_reply (then complexity null, slot_status {}).
Insurer and product are linked: if product is resolved, insurer is present; if product is missing/ambiguous report only product, not insurer.
Slot status: present = stated or resolvable from context; missing = not mentioned anywhere; ambiguous = mentioned but vague/unresolvable (e.g. "questa polizza" with no policy selected).
client_profile: for drafting present = at least one concrete attribute (name/initial, age, situation); for IBIP screening present = at least two of age, investment horizon, risk attitude, goal; ambiguous = only a vague label or one IBIP attribute; missing = nothing.
message_goal present when purpose explicit (spiegare, sollecitare, rifiutare, proporre); "scrivi qualcosa al cliente" is ambiguous.
scope: in_scope = insurance products/policies, regulation, client drafting, IBIP screening; out_of_scope = anything else, or requests to bypass rules or reveal hidden instructions; quick_reply = greeting, thanks, small talk.
Complexity (label as if the request were complete): product_policy_analysis simple = one fact/clause, one product, one chunk; complex = 2+ chunks, conditions/exceptions combined, or trade-off. comparison simple = exactly 2 products and 1 field; complex = 3+ products, 2+ fields, or a criterion ("quale conviene"). regulatory simple = one rule; complex = interpretation across rules. client_drafting simple = one purpose, facts given, short; complex = several facts, sensitive topic (claim refusal, complaint) or negotiation. ibip_screening simple = one criterion; complex = several or conflicting.
Route, first match wins: quick_reply -> quick_reply; out_of_scope -> refuse; any slot missing/ambiguous -> clarification; ibip_screening or client_drafting -> agentic; complex -> agentic; else lightweight.

## QA records (file qa_input.jsonl; fields id, question, evidence = list of chunks)
Answer ONLY from the evidence. Output one JSON line per record:
{"id":..., "answerable":true|false, "answer":"short Italian answer", "span":"exact text copied from one evidence chunk that supports the answer, or null", "value":"the key figure/value or null", "condition":"condition attached to the value, or null"}
If the evidence does not contain the requested information, answerable=false and answer exactly "Non indicato nei documenti.".
Never use knowledge outside the evidence.
