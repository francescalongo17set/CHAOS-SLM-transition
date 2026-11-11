# Hand-off: synthetic data build for the JEV-wise router and the answer writer

Last updated: 11 Nov 2026, late night (rewritten as one current document; the earlier session-by-session sections were merged). Stage 7 (bulk writing) is **in progress and paused**: 2,599 of 4,500 records are written (owner stopped the writers after list 032; 1,241 Sonnet jobs pending). Retrieval frozen: bge. Retrieval server STOPPED. Owner: Antonio Ponti (Team CHAOS, Navisio challenge).
Read this file first, then the guideline book. Do not start from the old data plan.

## 1. Goal
Build 4,500 synthetic Italian records end to end: Dataset 1 (3,000 router examples) and Dataset 2 (1,500 question-answer examples), from three insurance PDFs (Zurich Salute, Generali Immagina Adesso, Zurich Impresa) plus the names of two IBIP products (Italiana R&I+, Allianz Periodical4Life). The agent extracts, chunks, indexes, plans, writes, validates and packages the data. The specification is the **guideline book v0.2**: `data-generation/instructions/Guideline_book_v0.2_synthetic_data_for_the_JEV-wise_router_and_the_answer_writer.md` (sections 2 to 12 say what to write, 13 to 16 are the build playbook). The book wins over any older document in `instructions/`.

## 2. Rules that must not be forgotten
- **Draft mode (10 Nov 2026).** Gates G1 to G4 do not stop the work: the agent writes `logs/gate_Gx.md`, sets `auto_approved: true` and continues. Every record keeps `verified: false`, `release_status: draft_unreviewed`. G1 to G3 are written (G3 approved by the owner); G4 comes at stage 9.
- **Noise is acceptable (owner, 11 Nov 2026):** the aim is 4,500 usable samples, not perfect ones. Do not add strictness: borderline `client_profile` / `message_goal` labels and the 40% sampled blind pass are accepted. Still replace absent QA that the blind pass shows are NOT absent.
- **No invention** (every figure in an answer comes from a supplied chunk). **No hand edits** (a bad record is regenerated through its job). **Test isolation** (Zurich Impresa chunks, the Allianz name and the id `allianz_periodical4life` only in test jobs and `final/test_package/`). Global seed **20261110**.
- Out of this build: calibration split for tau, pseudonymisation, trainer-format conversion.
- Writers are sub-agents: Sonnet writes everything except 107 easy no-document jobs written by Haiku (`plan/writer_assignment.json`). Each agent must read its **own** model id from its system prompt and pass it as `--writer`. Blind labellers are Sonnet sub-agents. Same-model risk (Claude writes and checks) goes into the data card.
- **Agent rules (owner):** at most 3 agents at a time; memory is a concern (one shared retrieval server, never a model per process); do not launch rounds unprompted; no long sleep loops; stop the server when idle (`pkill -f retrieval_server`, check `ps aux | grep retrieval_server`).

## 3. Environment
- Layout: everything under `data-generation/data/` (the book says `navisio_data/`). PDFs in `raw/`. Git branch `data-generation`, nothing committed (`data-generation/` untracked).
- Conda env `navisio`, Python 3.11.18, interpreter `/Users/antonioponti/miniconda3/envs/navisio/bin/python`; packages in `code/requirements.txt`. Run scripts from `data/` as `python -I code/<script>.py`.
- macOS: no `timeout`; `sed -i ''`; use Python for file edits. HF cache `~/.cache/huggingface`.
- Retrieval server (needed by `write_batch.py` for QA jobs and by `verify_prepare.py`): `nohup /Users/antonioponti/miniconda3/envs/navisio/bin/python -I code/retrieval_server.py > logs/retrieval_server.log 2>&1 &` from `data/`, wait about 40 s for "ready" in the log. `retrieve()` uses it automatically.

## 4. Done: stages 0 to 6
| Stage | Script | Output | Result |
| --- | --- | --- | --- |
| 0 Setup | manual | `logs/env.json`, `logs/stage_0.md` | page counts 53/140/188 |
| 1 Extract | `extract.py` | `extracted/` | 3 of 140 Generali pages low-text |
| 2 Chunk | `chunk.py` | `chunks/chunks.jsonl` (1,019 chunks) | Salute 164, Generali 319, Impresa 536 |
| 3 Catalogue | `catalogue.py` | `catalogue/` | gate G1 |
| 4 Index | `embed.py`, `retrieve.py` | `index/`, `retrieval_config.json` | e5 and bge built; **bge frozen** |
| 5 Plan | `make_profiles.py`, `make_seeds.py`, `plan.py` | `seeds/`, `plan/jobs.jsonl` (2,064 jobs) | 69/69 assertions; gate G2 |
| 6 Pilot | `pilot_select.py`, `validate.py`, `write_batch.py`, ... | `pilot/stg`, `pilot/pilot_report.md` | 67 jobs; gate G3 approved |

Logs per stage in `logs/stage_N.md`; deviations and planner interpretations in `logs/gate_G1.md`, `gate_G2.md`, `gate_G3.md`. Pools: Salute train 132 / validation 32 chunks (validation = "Sezione 3 - Assistenza"); Generali train 267 / validation 52 ("Prevenzione e assistenza CASA"); Impresa test 536.

**Plan file.** `plan/jobs.jsonl`: 1,868 chunk jobs (optional QA record plus 0 to 2 router records) and 196 no-document jobs (up to 10 router records of one scenario). Each record has `fixed` (copied by code), `hints` and `seeds`. The writer writes query, history, resolved_slots, and for QA question, risposta, fonte, gold_value, gold_condition, difficulty. The live file differs from `plan.py` output by 4 absent-topic replacements (`plan/replacements.md`, `plan/replaced_jobs_archive.jsonl`, `code/replace_absent.py`, idempotent). Live sha256 starts 8539e390; after any `plan.py` re-run apply `replace_absent.py`.

## 5. Stage 7: how writing works now (bulk configuration)
- **Writer card:** `writer_card.md` (v2: complexity section, history shape, retrieval note). Validator `code/validate.py` 0.2 (blocking rules plus non-blocking `warn:` lines). Job notes `code/job_notes.py` (`>>` lines).
- **One command per batch:** `python -I code/write_batch.py <batch.jsonl> --dir staging/bulk/<NAME> --writer <model id>` validates, runs the retrieval pre-check (bge top 5; multi_fact = any gold chunk; all-gold and ranks logged in `<dir>/retrieval.jsonl`; `--no-check` skips), caches the request in `cache/writes.jsonl` and stages accepted records (`accepted_router.jsonl`, `accepted_qa.jsonl`, `job_status.json`, `rejected.jsonl`, `warnings.jsonl`). Bundles (qa_*, pairs_*, router_only_*) are accepted all-or-nothing.
- **Waves:** `python -I code/bulk_waves.py [--size 12] [--writer sonnet|haiku]` writes `staging/bulk/waves/<writer>_NNN.txt` (lists of 12 jobs grouped by scenario; finished jobs drop out). Launch an agent with `staging/bulk/agent_prompt.md` (placeholders LIST and NAME): it reads only the writer card, prints jobs with `show_job.py` / `brief.py`, writes records one by one (NO scripts, loops or templates: a script-made batch was discarded on 11 Nov), runs `write_batch.py`, reports in 5 lines. Check every returned batch for distinct queries and no generator scripts before accepting.
- **Token measures applied:** one call per batch, 2 seeds printed, lists of 12 jobs, minimal prompt, terse reports, sampled blind pass. A full API/Batches driver was rejected by the owner.
- **Blind pass:** `python -I code/verify_prepare.py <accepted_dir> <out_dir> <map.json> --shards 3 --sample 0.4` (absent QA always included; needs the server), 3 Sonnet labellers using `verify/definitions.md` (no scripts), then `python -I code/verify.py <accepted_dir> <verify_dir> <map.json>`. Last run: `verify/bulk2/`.
- `qa_check.py`, `hit5.py`, `embed_ctx.py`, `pilot_retrieval.py`, `trial_select.py` are older helpers; `qa_check.py` is no longer needed by writers.

## 6. Counts (11 Nov 2026), merged and deduplicated by record id
| | Target | Written | Left |
| --- | --- | --- | --- |
| Dataset 1 router | 3,000 | 2,038 | 962 |
| Dataset 2 QA | 1,500 | 561 | 939 |
| Total | 4,500 | 2,599 | 1,901 |

By split (plan / written): router train 2,100/1,301, validation 300/186, test 600/375; QA train 850/57, validation 150/9, test 500/33. Sources: pilot 311 router + 12 QA (`pilot/stg`); trial 452 router + 30 QA (`staging/trial/final`, includes 97 regenerated router records); bulk batch 1 23 router + 53 QA (`staging/bulk/final_b1`); bulk batch 2 1,076 router + 4 QA (`staging/bulk/final_b2`: all 70 Haiku jobs in `w_haiku_001..006` and Sonnet lists `w_sonnet_001..004`). Stage 8 will drop retrieval misses, duplicates and contamination hits, so final counts will be slightly lower.
Bulk batch 3 (`staging/bulk/final_b3`, 11 Nov night): 176 router + 462 QA from 41 agent lists (all done; 26 jobs skipped for retrieval misses, listed in `final_b3/job_status.json`, back in the pool). `job_status.json` of the older per-writer folders is consolidated in `final_b2/job_status.json`.
**Pending:** 1,241 Sonnet jobs = 104 lists of 12 (`bulk_waves.py`; it reads done jobs from every `job_status.json` under `staging/`, so never delete those). Skipped jobs (mostly answerable QA whose gold chunk is not in the bge top 5: near-duplicate and table chunks, 5-word telegraphic questions) are in the pool; the writer prompt now tells agents to keep telegraphic questions to the minimum words with the most distinctive terms and never to resubmit accepted jobs.

**Blind pass on absent QA of batch 3 (`verify/absent3/`, 272 absent QA in 9 shards):** 16 marked answerable by the labellers (list in `verify/absent3/answerable_qa_ids.json`; qa-000748 and qa-000751 are borderline). Topics that keep coming back answerable: 'periodo di osservazione' (qa-000299, 813, 814, 815), 'premio non goduto' (843, 844), 'riattivazione' (837, 839). Not yet dropped or replaced: run `replace_absent.py` with new topics, then blind-check the replacements. qa-000260 is still open too.

## 7. Quality so far
- Pilot (323 records): validator first pass 91%; blind route 95.2%, slot_status 96.2%, complexity 84.5% (accepted at G3); hit@5 44 to 56% (bge) before the pre-check.
- Trial (97 jobs, 482 records): first pass 99.0%; hit@5 all-gold 0.833, any-gold 0.958 (24 answerable QA). After prompt revision 2 the complexity agreement of the regenerated jobs rose from 40% to 92.8%.
- Bulk batch 1 (50 QA jobs): first pass 98%, hit@5 0.947; one absent QA failed (see section 8).
- Bulk batch 2 blind pass (413 router + 4 QA sampled): scope_check 99.0%, feature 99.3%, complexity 97.1%, slot_status 92.2%, route 93.7%, qa_answerable 3/4. Disagreements are mostly `client_profile` / `message_goal` (missing vs ambiguous). Details in `logs/stage_7.md`.
- Complexity for `client_drafting` and `ibip_screening` is not counted against the 90% target (they always route to agentic; owner decision, labels unchanged).

## 8. Known issues and open items
1. **Absent QA that are not absent.** Keyword zero-hit topics are not enough: batch 1 had topic 'rateazione e frazionamento del premio' (replaced, jobs 833 to 836) and 'periodo di osservazione' (replaced); batch 2 has **qa-000260 (Zurich Salute, 'cambiare piano o forma di copertura') which is answerable** and still needs a drop and replacement through `replace_absent.py` (add a round, new topic, confirm by blind pass). Run the blind pass on every absent QA in bulk and replace failures. About 90 other topic/family pairs are unconfirmed.
2. **Four scope disagreements in batch 2** to read: orc-002690, orc-002682, orc-001633, orc-001747 (`verify/bulk2/disagreements.csv`).
3. **Planner defects** (conflicting pair hints, comparison jobs with a document not in `available_docs`, follow_up history chunks): the writer card has workarounds (skip when a hint cannot be met); see `logs/gate_G3.md`.
4. **multi_fact scoring:** pre-check uses any-gold; stage 8 should record any-gold plus rank and report all-gold separately.
5. **qa_value metric** (crude string match) must be replaced by a blind-labeller equivalence judgement before the quality report.
6. **date_reference slot:** `verify/definitions.md` now says it is required only when the answer depends on a date; the plan marks about 25% of regulatory requests as needing it.
7. **Diversity:** IBIP and drafting jobs have limited wording room (openings repeat, e.g. "Italiana R&I+ per..." 13 times in one list). Run the diversity check every 300 records during bulk.
8. Salute train chunks are reused up to 5 times; writers skip when no further distinct fact exists. Impresa absent topics are tight (21 usable x 5 = 105 for 100).
9. Model ids: Haiku batches carry `claude-haiku-5-5`; Sonnet batches carry `claude-sonnet-5-5` (read by the agents). The pilot and trial records may carry aliases (`subagent-*-alias`) or `claude-sonnet-5-5` for Haiku pilot artefacts: normalise at stage 8.

## 9. Remaining stages
- **Stage 7 (continue):** write the 145 Sonnet lists (QA jobs need the server), 3 agents at a time; replace failed absent QA; diversity check every 300 records; regenerate rejected jobs up to 3 times.
- **Stage 8 post-process** (`postprocess.py` to write): retrieval fills evidence_record, retrieval_hit, gold_rank; drop retrieval misses and plan replacements; hard negatives; pairs; de-dup; 13-word n-gram and edit-distance contamination filter; normalise generator ids.
- **Stage 9 verify:** sampled blind pass, review queues, quality report, gate G4. `verify.py` exists.
- **Stage 10 package** (`package.py` to write): `final/train`, `final/validation`, `final/test_package` separate, `manifest.json` with SHA-256, data card, README with the run order.

## 10. File map (`data-generation/data/`)
```
raw/ extracted/ chunks/ catalogue/ index/    stages 1 to 4
seeds/ plan/                                 stage 5 (jobs.jsonl, STATE.json, writer_assignment.json, replacements.md)
pilot/        pilot_report.md, pilot_jobs.txt, qa_all.jsonl, retrieval_compare.json, stg/ (accepted pilot records)
staging/trial/{all,final}, staging/regen/{all}   trial and regenerated records (final = merged set)
staging/bulk/ agent_prompt.md, all_b1/, final_b1/, final_b2/ (+ job_status.json), final_b3/ (accepted_*, job_status.json, retrieval.jsonl), repl_check*/, waves/ (regenerated by bulk_waves.py; do not run it while agents read the lists). Per-writer folders were merged and deleted on 11 Nov night; per-batch inputs are recoverable from cache/writes.jsonl
verify/       definitions.md; pilot/, trial/, regen/, bulk1/, bulk2/ (blind-pass inputs, outputs, disagreements.csv, map.json); repl/, repl2/; absent3/ + absent3_map.json (qa_input, qa_output, answerable ids)
cache/writes.jsonl   every submitted batch (the per-batch files were deleted on 11 Nov; recover from here)
code/         extract chunk catalogue embed retrieve retrieval_server make_profiles make_seeds plan replace_absent
              validate write_batch show_job brief job_notes bulk_waves verify_prepare verify hit5 qa_check ... requirements.txt
logs/         env.json, stage_0..7.md, gate_G1..G3.md, server logs
writer_card.md   HANDOFF.md (this file)
```
Cleanup of 11 Nov removed about 440 files (per-batch `b*.jsonl`, writer scripts, stray Haiku trial artefacts, the discarded templated batch, wave lists, `__pycache__`); records are untouched. Old trial intermediates (`staging/trial/all`, `staging/regen/all`, `staging/bulk/all_b1`) stay on disk by owner decision.

## 11. First actions for the next agent
1. Read this file, book sections 1, 4 to 7, 9, 10, 16, `logs/gate_G3.md`, `logs/stage_7.md`.
2. Check state: `wc -l plan/jobs.jsonl` (2,064), `ps aux | grep retrieval_server` (should be empty), `python -I code/bulk_waves.py` (1,730 Sonnet jobs pending).
3. Ask the owner before launching writers; then start the server, build waves, launch at most 3 agents, check each returned batch, stop the server when done.
