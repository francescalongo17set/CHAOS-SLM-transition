# Gate G4 (stage 9) - auto_approved: true (draft mode)

Date: 13 Nov 2026. Draft mode: not reviewed by a human; every record `verified: false`, `release_status: draft_unreviewed`.

## Final merged set (`post/`)
router 2,983 (train 2,092 / validation 298 / test 593) + QA 1,485 (train 842 / validation 150 / test 493) = **4,468 of 4,500**. Routes: lightweight 923, agentic 806, clarification 508, refuse 478, quick_reply 268. QA: 1,188 answerable + 297 absent. Writers: Sonnet 2,562 records, Haiku 1,906.
hit@5 (bge, answerable QA, any-gold): 1.000 in all splits (pre-check filter); all-gold 0.868 train / 0.858 validation / 0.859 test.

## Done at stage 9
- Dropped (via `plan/superseded_qa.json`, applied by `postprocess.py`): qa-000627, qa-001223 (haiku3 not answerable); orc-001633, orc-002682 (batch 2 scope disagreements read and judged wrong); orc-001747 and orc-002690 kept (borderline).
- Diversity check: `code/diversity.py`, `post/diversity.md`. Duplicate rate 0 everywhere. **Every cell exceeds the 5% same-first-word limit** (QA: product name first, e.g. "Zurich" 20-25%; client_drafting "Scrivi" 30-32%; IBIP "Italiana" 14-18%; comparison/lightweight "e" 20%). Not regenerated (draft mode).
- Blind pass on a 25% sample of records never labelled before (`verify/final/`, 323 router + 179 of 213 QA; the QA labellers were stopped by the owner, 34 QA unlabelled): scope 99.7%, feature 97.8%, complexity 93.2%, slot_status 93.7%, route 94.4%, qa_answerable 99.4%, qa_span 88.8% (below 90%: note), qa_value 86.0% (crude string match, not an accuracy).
- Review queues in `review/` (test router, test QA, leaked unsafe, all absent QA, 20% train/validation sample); decision columns empty.

## Open items
1. Unsettled test questions (30, book section 9) never built: deviation, owner to decide.
2. About 1,000 router and about 660 QA records were never blind-checked (earlier passes cover 2,309 records; this one a 25% sample). Earlier passes used the strict coverage definition (inflated disagreements).
3. Diversity cells over 5% (above).
4. 32 records short of 4,500 (52 jobs skipped twice dropped, replacement-round skips, Impresa Furto cap, stage 9 drops).
5. Same-model risk, QA wording echoes chunks (retrieval pre-check), Haiku share, telegraphic comparison convention: for the data card.
6. Reviewer names and sharing (book section 12) and training-rights confirmation: owner.
7. Retrieval server may still be running (`pkill` was denied in this session): stop it with `pkill -f retrieval_server`.
