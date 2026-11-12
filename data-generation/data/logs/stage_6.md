# Stage 6 log: pilot (COMPLETE 11 Nov 2026; gate G3 written and approved by the owner, see logs/gate_G3.md and pilot/pilot_report.md)

Date: 10 Nov 2026. Writer: claude-sonnet-5-5 (this session). Seed 20261110.

## What was done
- `code/pilot_select.py` picked 67 jobs (3.2% of jobs, 323 records = 7% of records), stratified: at least 3 per scenario, leak type/difficulty, modifier, context scenario, QA type (`pilot/pilot_jobs.txt`).
- Writer output format changed (deviation): the writer emits ONLY written fields; code merges the fixed fields from the job (`code/validate.py: assemble`). Lines: router `{job_id,kind,query_id,query,history,resolved_slots}`, qa `{job_id,kind,qa_id,question,risposta,fonte,gold_value,gold_condition,difficulty}`, skip `{job_id,kind:"skip",reason}`.
- `code/validate.py` (VALIDATOR_VERSION 0.1) implements book s.10 plus planner interpretations (telegraphic 2-4 words / QA exactly 5, pair diff <= 8 words, 12-word copy check, fonte verbatim, numbers in risposta in gold chunks, assistant history numbers in history chunk, absent exact string, label-name leak, language, PII, forbidden chars).
- `code/write_batch.py` validates a batch file, caches it in `cache/writes.jsonl`, appends accepted records to `<dir>/accepted_{router,qa}.jsonl`, rejects to `<dir>/rejected.jsonl`, tracks `<dir>/job_status.json`. Bundles (qa_*, pairs_*, router_only_*) are accepted all-or-nothing; other no-document jobs per record. `--replace` drops earlier accepted ids and re-accepts.
- Pilot staging dir: `pilot/stg/` (311 router + 12 QA accepted). Batches `pilot/b01..b33.jsonl`; `mk28/30/31/32.py` generated several batches.

## Results so far
- Validator first pass: 61/67 jobs (91%); target 80%. First-pass failures were 3 validator false positives (premium/target market/Periodical4Life digit; fixed in validator) and 3 writer errors (12-word copy x2, pair diff 9).
- Test isolation: no violation (Impresa/Allianz only in test jobs).
- hit@5 (`pilot/retrieval_compare.json`, 9 answerable QA, hit = all gold chunks in top 5): e5 0.444, bge 0.556 (any-gold 0.667 both). TARGET 85% MISSED. Cause: near-duplicate chunks (Generali Furto variants, Impresa Premium guarantees) and questions without distinctive terms; typo/telegraphic questions suffer most.
- Variant `e5ctx`/`bgectx` (embed `"{product} - {section_path}\n{text}"`, `code/embed_ctx.py`, `index/emb_*ctx.npy`, entries added to `retrieval_config.json`): e5ctx did not clearly help on 5 rewritten questions. A 4-model comparison on 12 questions (`pilot/qa_all.jsonl`, `code/qa_check.py`) was still running when this was written; result not recorded.
- Rewritten QA candidates for the 5 worst questions are in `pilot/b33.jsonl` (NOT yet accepted into staging; old versions are in `pilot/stg`). Several still miss under e5 (qa-000421, qa-000980). This is prompt revision 1 of 2.

## Not done yet
1. Freeze `index/retrieval_config.json` `active` (still the placeholder e5) after the 4-model result; apply the 2-point/fewer-dimensions rule.
2. Blind pass with a fresh-context sub-agent (untested). Prepared: `code/verify_prepare.py <accepted_dir> <out_dir> <map.json> --shards 2` and the definitions file in the session scratchpad (`.../scratchpad/blind/definitions.md`; copy it into `verify/` if the scratchpad is gone). Agreement target 90% per field.
3. `writer_card.md` (<= 2 pages), `pilot_report.md` (40 random rows), `logs/gate_G3.md`.
4. Decide the retrieval pre-check loop for stage 7 (see HANDOFF s.7).

## Planner defects / deviations found (log in G3)
- Comparison jobs where a compared document is not in `available_docs` (e.g. job-001031, job-001984 context).
- Pair hints that conflict inside a pair (topic or goal differs between members; job-001112, job-002035). The 8-word pair rule was followed and the text uses one topic/goal for both.
- follow_up/slot_clarified records resolve `coverage` (or `field`) from a history chunk unrelated to it. Convention used: the history gets one extra exchange that introduces the coverage; assistant turns carry no figures.
- Validator tuning made during the pilot: product names with digits, loanwords (target market, set informativo), English terms allowed when they appear in the chunk section path.

## 4-model retrieval result (rewritten questions, qa_check.py, 11 lines; qa-000980 listed twice)
Per-gold ranks in top 5, any gold chunk: e5 8/10 questions, e5ctx 8/10, bge 8/10, bgectx 7/10. All gold chunks in top 5 (multi_fact needs all): all four stay well under 85%. No model is clearly better; the section-title variants give no consistent gain (they help qa-000210/qa-001053, hurt qa-001222/qa-001227 for bgectx). Conclusion: the plain-chunk models are within noise of each other, so the 2-point rule picks e5 (768 dims) as `active` UNLESS the pre-check loop changes the picture; freeze it at the end of stage 6. The real fix is the writer-side pre-check (reword until gold is in top 5) and counting multi_fact by any-gold plus rank, to be decided in G3.
