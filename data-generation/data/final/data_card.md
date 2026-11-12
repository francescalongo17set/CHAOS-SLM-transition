# Data card: synthetic Italian insurance data (draft, unreviewed)

**Status:** `release_status: draft_unreviewed`; 0% of records human-verified. Seed 20261110. Built 10-13 Nov 2026.

## Contents
- Dataset 1 (router): 2,983 records (train 2,092, validation 298, test 593). Fields: query, context (history, selected_doc_id, available_docs, resolved_slots), labels (scope_check, feature, complexity, missing_info), support (slot status, expected_route, scenario, noise tags, source chunks, safety_leak, family, split, generator).
- Dataset 2 (QA): 1,485 records (train 842, validation 150, test 493): 1,188 answerable, 297 absent-answer. Fields: question, evidence_record (top-5 retrieved chunks, bge-m3), target (risposta, fonte, chunk_ids), support (type, expected_behavior, gold chunk, retrieval_hit, gold_rank).
- Sources: Zurich Salute and Generali Immagina Adesso (train/validation), Zurich Impresa (test only), plus names of two IBIP products (Italiana R&I+ in train; Allianz Periodical4Life only in the test package). Target was 4,500; 32 short.
- Test isolation: `test/` holds all Zurich Impresa material and the Allianz name; verified by assertion in `code/package.py`. Contamination filter: 13-gram and edit-ratio 0.90 against test.

## Label definitions
Written in `verify/definitions.md` (blind-labeller version) and the writer card `writer_card.md` v3. Route, first match wins: quick_reply, refuse (out of scope), clarification (any slot missing or ambiguous), agentic (IBIP, drafting, complex), else lightweight. A named field alone fills the coverage slot (owner rule 13 Nov). Leaked-unsafe rows: `support.safety_leak: true` (unsafe request that slips through a surface cue).

## Known risks and noise
- **Same-model risk:** Claude wrote the records (Sonnet 2,562, Haiku 1,906) and Claude checked a sample. No human review. Test set must not be used for reporting until reviewed.
- **Sampled checks only:** blind pass on about 40% (pilot to bulk) and 25% (final) samples; route agreement 91-100%, slot status 85-99%, complexity 84-99%, QA answerable 98-100%, span about 89%. Earlier passes used a stricter coverage definition, so their coverage/route disagreements are inflated.
- **QA wording echoes chunks:** many questions were reworded until they passed the retrieval pre-check (hit@5 any-gold 1.0; all-gold about 0.86); some QA difficulty defaults to medium.
- **Diversity:** every cell exceeds the 5% same-first-word limit (QA starts with the product name; drafting "Scrivi"; IBIP "Italiana"); no duplicates.
- **Planner defects:** comparison jobs with a second product missing from available_docs, lookup pairs with a second chunk (fixed only in replacement jobs). Telegraphic comparison queries put the second product in a history turn.
- Synthetic context windows (history turns are written, not real conversations). Haiku skipped/refused some lists early on; 52 jobs skipped twice were dropped.
- Deferred: human checks (review queues in `review/`, empty), 30 unsettled test questions (book section 9, not built), pseudonymisation, calibration split, trainer-format conversion.
- Training rights for the source PDFs: **to be confirmed by the owner.**
