# Stage 7 log (trial first)

Date: 11 Nov 2026.
- Trial: 100 non-pilot jobs chosen by `code/trial_select.py` (seed 20261110), lists in `staging/trial/jobs_*.txt`. Wave 1: Haiku writer (15 easy jobs) plus two Sonnet writers; wave 2: three Sonnet writers. Each writer has its own staging dir `staging/trial/w_<name>` (no shared status file) and passes `--writer` to `write_batch.py`.
- Shared retrieval server (`code/retrieval_server.py`) must be running; **STOP IT when the trial is finished** (`pkill -f retrieval_server`).
- Writer ids: sub-agents were started with aliases "haiku" and "sonnet"; exact model ids were not read from the sessions and are recorded as aliases in `generator`.

## Trial result (11 Nov 2026), 53 of 100 jobs written
Written: haiku_w1 15 jobs, sonnet_w1a 18, sonnet_w1b 18, sonnet_w2a 2 (stopped by the owner), sonnet_w2b 0 (stopped), sonnet_w2c not launched. Owner asked to launch no more rounds. Unwritten trial jobs: lists in `staging/trial/jobs_sonnet_w2*.txt`.
- Output: 336 router + 8 QA records, merged in `staging/trial/all/` (generator = `subagent-haiku-alias` 142, `subagent-sonnet-alias` 202).
- Validator first pass: 52 of 53 jobs (98.1%). One retry (a 5-word telegraphic router query, fixed in the second attempt).
- hit@5 (bge, with the writer pre-check, 7 answerable QA): all-gold 0.571, any-gold 1.0. All 3 conditional/single QA hit; 3 of 4 multi_fact questions missed at least one gold chunk (table-of-contents and sibling chunks). Multi_fact all-gold remains the weak point.
- Writer notes: pair jobs have conflicting hints between members (writers used the "a" member's profile/goal); follow-up pair members keep the product name to stay within 8 words.
- Blind pass and diversity check NOT yet run on the trial.
- Retrieval server stopped after the trial (`pkill -f retrieval_server`).

## Trial final (11 Nov 2026, second session): 97 jobs written
- Written: haiku_w1 15, sonnet_w1a 18, sonnet_w1b 18, sonnet_w2a 17, sonnet_w2b 17, sonnet_w2c 12 = 97 jobs (the planner's lists summed to 97, not 100). 452 router + 30 QA records, merged in `staging/trial/all/` (generator: `subagent-haiku-alias` 142, `subagent-sonnet-alias` 340).
- Validator first pass: 96 of 97 jobs (99.0%).
- hit@5 (bge, with writer pre-check, 24 answerable QA): all-gold 0.833, any-gold 0.958.
- Blind pass (3 Sonnet labellers + 1 QA answerer, `verify/trial/`): scope_check 99.1%, feature 99.1%, route 90.0%, slot_status 91.9%, complexity 55.3% (194/351), qa_answerable 30/30, qa_span 22/24, qa_value 66.7% (crude string metric).
- Complexity: 141 of 157 disagreements are recipe=complex vs blind=simple. Rescored on complete requests only: trial 62.8% (215) vs pilot 87.7% (130), so the "as if complete" artefact is NOT the whole story; asymmetric (simple labels agree ~90%, complex labels ~50%). See HANDOFF section 14.
- Haiku records (easy scenarios only): 9.2% had any disagreement vs 56.8% for Sonnet, but the Sonnet set contains the hard scenarios, so the two are not comparable.
- Server stopped after the blind pass (`pkill -f retrieval_server`); verify no `retrieval_server` process before leaving.

## Bulk batch 1 (11 Nov 2026): 50 QA jobs, two Sonnet writers (sonnet_b1a, sonnet_b1b)
- Written to `staging/bulk/w_sonnet_b1a` and `w_sonnet_b1b`, merged in `staging/bulk/all_b1/` (23 router + 50 QA records); generator `subagent-sonnet-alias`. Job lists: `staging/bulk/jobs_b1a.txt`, `jobs_b1b.txt`.
- Validator first pass 49/50 jobs (98%). hit@5 (bge, with pre-check) 36/38 = 0.947 (misses: qa-000018, qa-001307). Blind pass NOT run on this batch.
- Writer note: client profiles were not shown for QA-bundle jobs (hints only had `profile_id`); fixed below.

## Prompt revision 2 (11 Nov 2026) for the complexity gap, steps 1 to 3
- Cause found: complex comparison jobs hint one `field` plus `common_fields`, so writers produced 2 products + 1 field (= simple by book s.4); regulatory complex needs two interacting rules but writers asked about one.
- `code/job_notes.py` (new): complexity requirement and client profile per record; printed as `>>` lines by `show_job.py` and `brief.py`.
- `writer_card.md`: new section "Complexity: make the label visible in the text".
- `validate.py` 0.2: non-blocking `warn:` check for comparison complexity (logged in `<dir>/warnings.jsonl` by `write_batch.py`). On the trial's comparison records it flags 9 of 15 blind mismatches with 4 false alarms (13 flags).
- Not yet done: regenerate the mismatched comparison/regulatory trial jobs and re-run the blind pass on that slice (about 20 jobs) to measure the effect.

## Regeneration test of prompt revision 2 (11 Nov 2026)
- Jobs: the 20 trial jobs holding 36 records labelled complex (comparison / regulatory_consultation) that the blind pass read as simple; whole jobs regenerated (97 records, same ids) by two Sonnet writers with the revised card and `>>` notes, in `staging/regen/` (merged `staging/regen/all/`). Validator: all 20 jobs accepted; 3 jobs needed a second attempt (telegraphic word count, one complexity warning). Blind pass: 2 Sonnet labellers, `verify/regen/`.
- Complexity agreement on the 97 regenerated records: 39/97 (40%) before, 90/97 (92.8%) after. The 36 target records: 34/36 now agree (21/21 complete requests, 13/15 with a missing/ambiguous slot). Complete requests: 16/37 before, 37/37 after. Comparison 1/16 -> 16/16; regulatory 21/44 -> 42/44.
- Same records, other fields: route disagreements 30 -> 23 records, slot_status 30 -> 38 (mostly date_reference where the blind labeller does not list the slot as required, and borderline client_profile ambiguity; not tied to the new card), feature 0 -> 1, scope_check 0 -> 0.
- Caveats: the "before" set was selected for mismatching, so 40% is not a typical rate (trial overall was 55.3%); writers were handed the same definitions the labeller uses, so the gain shows the labels are now visible in the text, not an independent validation; same-model writer and labeller; clarification records still hide complexity from a text-only checker.
- Decision pending for bulk: keep the revised card and `>>` notes (clear gain, no sign of harm). Replace the trial records of these 20 jobs with the regenerated ones in the final merge (old versions stay in `staging/trial/`).

## Owner decision (11 Nov 2026, night)
Keep the revised writer card, `job_notes.py` and validator 0.2 as the bulk configuration. Regenerated records replace the old trial records of the same ids: merged trial set in `staging/trial/final/` (old versions kept in `staging/trial/all/`, `staging/regen/`).

## Blind pass on bulk batch 1 (11 Nov 2026, night): 23 router + 50 QA, `verify/bulk1/`
- Router (23 records): scope_check 100%, feature 100%, complexity 91.3% (21/23), slot_status 96.6% (84/87), route 82.6% (19/23). Small sample.
- QA (50): qa_answerable 49/50 (98%). qa_value 78.9% and qa_span 84.2% are from a crude string metric; reading all 14 flagged cases, about 12 are false alarms (equivalent wording such as "inferiore a 16 anni" vs "under 16", "€ 3.000" vs "3.000 euro", multi_fact gold values listing several facts where the blind answer covers them in the sentence). Ambiguous: qa-000060 ("neonati gratuiti?", gold value is the 60-day condition while the blind answer says "gratuita").
- **Real error: qa-000833 (absent).** Topic "rateazione e frazionamento del premio" for generali_immagina_adesso is NOT absent: the evidence lists monthly, quarterly and half-yearly instalments with surcharges. The same topic is used by 4 planned absent QA (jobs 833, 834, 835, 836). Absent topics were zero-hit on keywords only (HANDOFF s.6), and "frazionamento" is not the word the document uses ("rate", "trimestrali").
- Action proposed (not done): drop or regenerate the 4 absent QA of that topic (no hand edits; a replacement job with a confirmed absent topic), and check every absent QA of the bulk run with the blind pass, since this batch shows about 1 in 12 absent questions may not be absent (300 absent QA in the plan, 94 distinct topic/family pairs).
- The qa_value metric should be replaced by a blind-labeller equivalence judgement before the quality report.

## Absent-topic replacement (11 Nov 2026, night), owner request: drop the 4 absent QA and replace them
- Dropped: the 4 absent jobs 833 to 836 (topic 'rateazione e frazionamento del premio', generali_immagina_adesso; only qa-000833 had been written). Replaced through the plan by `code/replace_absent.py` (hints only: topic, terms, angle 5; old versions in `plan/replaced_jobs_archive.jsonl`; log and hashes in `plan/replacements.md`).
- New topics (Norme Comuni, train): 833 arbitrato, 834 coassicurazione, 835 duplicato della polizza, 836 interessi di mora. Each checked by synonym search over all Generali chunks (0 real hits), at most 5 uses per topic.
- Round 1 used 'periodo di osservazione' for 835; the blind pass found it is NOT absent (the document has a 'Termine di aspettativa' for natural events, a waiting period under another name). Replaced in round 2 by 'duplicato della polizza'; the blind pass on the new qa-000835 returned 'Non indicato nei documenti.'. Blind pass on the other three: all absent. Lesson: a keyword or synonym check is not enough; run the blind pass on every absent QA and replace failures through the plan.
- Records: `staging/bulk/w_repl_absent` (833, 834, 836 used; its 835 superseded), `staging/bulk/w_repl_absent2` (835). Merged batch 1: `staging/bulk/final_b1/` (23 router + 53 QA; qa-000833 replaced, 834 to 836 added). The old qa-000833 stays in `staging/bulk/all_b1/`, not used.
- Plan hash: jobs.jsonl sha256 is now 8539e3907c89... (was 3cedeaa2...). `plan.py` no longer reproduces it; re-apply `replace_absent.py` after any re-run.
- 2026-11-11 w_sonnet_003 (12 jobs, 98 router records) discarded: agent generated records with a script from templates (repeated openings, duplicated profiles). Moved to rejected/w_sonnet_003_templated; jobs back in the pending pool. Prompt now forbids scripts.
- sonnet_001: 12 jobs, 120 router records accepted (5 first-attempt rejects, fixed); queries all distinct, varied. History shape added to writer card.

## Blind pass on bulk batch 2 (11 Nov 2026, night): `staging/bulk/final_b2/` (1,076 router + 4 absent QA from the 4 Haiku-free Sonnet lists and 6 Haiku lists), sample 40% = 413 router + 4 QA, `verify/bulk2/`
- 3 Sonnet labellers (no scripts), shards of 138; labeller differs from the Haiku writer, same model as the Sonnet writer (same-model risk).
- Agreement: scope_check 99.0%, feature 99.3%, complexity 97.1% (241), slot_status 92.2% (459 slots), route 93.7%, qa_answerable 3/4.
- slot_status disagreements 36: client_profile 18 and message_goal 12 (missing vs ambiguous, mostly drafting/IBIP), topic 3, date_reference 2, product 1.
- Route disagreements 26: mostly clarification vs agentic (the slot_status borderline above); 4 scope disagreements (orc-002690, 002682, 001633, 001747; refuse/quick_reply/lightweight edge cases) to read.
- **Absent QA qa-000260 is NOT absent** (Zurich Salute: 'cambiare piano o forma di copertura a contratto in corso'; the document says policy changes are possible in writing). Needs drop and replacement through `replace_absent.py` (same as jobs 833 to 836). Not done yet.

## Bulk batch 2 writing and token optimisation (11 Nov 2026, night)
- Changes: `write_batch.py` runs the retrieval pre-check itself (any-gold for multi_fact, ranks in `retrieval.jsonl`, `--no-check`); `show_job.py` prints 2 seeds; `code/bulk_waves.py` (lists of 12 jobs by scenario); `staging/bulk/agent_prompt.md` (minimal agent prompt, no scripts, 5-line report); `verify_prepare.py --sample`; `verify.py` skips unsampled records; `verify/definitions.md` date_reference rule; writer card history shape.
- Written: all 70 Haiku jobs (`w_haiku_001..006`, 700 router records, `claude-haiku-5-5`) and Sonnet lists 001 to 004 (376 router + 4 absent QA). First-attempt rejects were few (0 to 5 records per list): history field name, telegraphic word count, resolved_slots mismatch, pair word-diff over 8 words, language flag. The first `w_sonnet_003` was discarded (98 records made with a script from templates) and rewritten by hand; job-001170 was left unwritten by its agent.
- Merged set `staging/bulk/final_b2/` (1,076 router + 4 QA); blind pass result above. Counts after this batch: 1,862 router + 99 QA = 1,961 of 4,500.
- Cleanup: about 440 redundant files deleted (see HANDOFF section 10). Retrieval server stopped.
