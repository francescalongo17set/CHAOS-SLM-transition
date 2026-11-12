# Gate G3 (pilot) - NOT auto-approved

Date: 10 Nov 2026. Status: `auto_approved: false`; APPROVED BY OWNER (Antonio Ponti) on 10 Nov 2026 with the decisions below. Two targets are missed (blind complexity agreement 84.5% vs 90%; hit@5 all-gold 66.7% vs 85%). Prompt revision 1 of 2 is used. Book section 14: if a target is still missed after two revisions, stop and report. Stage 7 should not start until the owner (or revision 2) resolves the items below.

## Decisions taken
- Retrieval frozen: `active = bge` (BAAI/bge-m3, 1024 dims). It beats e5 by more than 2 points (all-gold 0.667 vs 0.444, any-gold 0.889 vs 0.778, n=9; small sample).
- Writer card: `writer_card.md`. Pilot report: `pilot/pilot_report.md`.
- Blind pass with fresh-context sub-agents tested and works (`code/verify.py`, `verify/definitions.md`, `verify/pilot/`).

## Proposed for owner decision
1. Complexity agreement: blind check cannot see "as if complete" for requests with missing slots. Either score complexity only on records with all slots present, or accept the gap and send client_drafting to human review. Review the 26 disagreements in `verify/pilot/disagreements.csv`.
2. hit@5: add the writer-side pre-check (reword until gold is in top 5 with bge, drop after 3 tries) and report first-attempt hit@5 and yield; define multi_fact hit as any-gold plus rank, with all-gold reported separately.
3. Bulk writing (~2,000 jobs) through fresh sub-agents on separate job ranges is still untested for writing (only labelling tested).

## Planner defects (carry into the data card)
- Comparison jobs where a compared document is not in `available_docs` (job-001031, job-001984).
- Pair hints conflicting inside a pair (job-001112, job-002035).
- follow_up/slot_clarified records resolve coverage/field from an unrelated history chunk; convention: an extra history exchange introduces it.
- `write_batch.py`: a bundle job resubmitted with missing lines is left pending without a logged rejection.

## Open checks for humans
- qa-000421 (blind 20.000 vs gold 50.000,00 euro).
- All absent QA topics (keyword zero-hit only).

## Owner decisions (10 Nov 2026)
1. Complexity agreement 84.5%: accepted as is. Keep the client_drafting/ibip_screening complexity disagreements as a data-card note and a human review queue.
2. hit@5 below target: accepted for now. The writer-side pre-check stays proposed for stage 7 and first-attempt hit@5 must be reported.
3. qa-000421 checked by the owner: the answer is good (50.000,00 euro stands; the blind pass was wrong). Flag `verified` is left false until a reviewer name is recorded per book s.11.

## Haiku writer trial (11 Nov 2026) and decision
- Trial: Haiku sub-agents wrote 48 of the 67 pilot jobs (206 router, 8 QA); the 19 jobs of shard c were not written (stopped by the owner for memory). Validator first pass 48/48. Blind pass by Sonnet sub-agents (`verify/haiku/`): scope 99.5%, feature 99.5%, route 91.7%, slot_status 89.5%, complexity 60.7%, qa_answerable 8/8. hit@5 (bge, with writer pre-check) 5/6. Sonnet pilot: route 95.2%, slot_status 96.2%, complexity 84.5%.
- Weak cells for Haiku: agentic_client_drafting (18 of 22 records with a disagreement), clarification_missing_slot (7 of 9), agentic_ibip_screening (6 of 18).
- **Owner decision (option a):** Haiku writes only the easy no-document scenarios: quick_reply, refuse_out_of_scope, refuse_leaked_unsafe, lightweight_regulatory_lookup, pairs_leaked (107 of 2,064 jobs, about 5%). Sonnet writes everything else. Assignment per job: `plan/writer_assignment.json`.
- Caveats: small n per scenario (11 to 50 records); the Haiku set lacked shard c; QA quality for Haiku not judged beyond hit@5.
- Provenance: `generator` is stamped from the job, so trial records carry `claude-sonnet-5-5` wrongly (trial files only, not dataset). `write_batch.py --writer <id>` now overrides it; it MUST be used for every Haiku batch. The exact Haiku model id was not read from a session: record it from the run before bulk use (sub-agents were started with the alias "haiku").
- The data card must name both writers and the same-model risk for the blind pass (Sonnet).
