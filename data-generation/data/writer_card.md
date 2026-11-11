# Writer card (v2, bulk configuration): how to write one job

Read the job with `python -I code/show_job.py job-XXXXXX` (or `brief.py` for no-document jobs). Write ONLY the written fields. Code merges the fixed fields. Everything is Italian, natural, as a broker or client would type. **Write every record yourself, one by one: never generate records with a script, loop, template or string substitution (such batches are discarded).**

## Output lines (one JSON per line, always with job_id)
- Router: `{job_id, kind:"router", query_id, query, history, resolved_slots}`
- QA: `{job_id, kind:"qa", qa_id, question, risposta, fonte, gold_value, gold_condition, difficulty}`
- Skip: `{job_id, kind:"skip", reason}` when the chunk has no further distinct fact (`fact_index`) or no honest question exists.
Batches of at most 10 records. Submit with `python -I code/write_batch.py batch.jsonl --dir staging/bulk/<NAME> --writer <your exact model id>` (the lead gives NAME; read your model id from your system prompt). Bundle jobs (qa_*, pairs_*, router_only_*) are accepted all or nothing: resubmit EVERY line of the job (QA and router), not only the one you fixed.

## Hard rules
1. **No invention.** Every figure, condition and name in a risposta comes from a supplied chunk. Assistant turns in history contain no figures.
2. **Fixed fields are copied by code.** Respect `selected_doc_id`, `available_docs`, `resolved_slot_keys`; never contradict them.
3. **Test isolation.** Impresa chunks, "Allianz" and `allianz_periodical4life` only in test jobs.
4. **No 12-word run copied from a chunk.** Reword answers; lists in chunks are the usual culprit.
5. **fonte is verbatim** from the chunk (keep its curly apostrophes and spacing), a short span that contains the gold value.
6. **No label names** in the text (scope_check, in_scope, feature names, route names). No real personal data, no emails, phone numbers.
7. **English terms** only when the job has the code_mixed modifier or the term is in the chunk's section path (loanwords such as "target market", "set informativo" are fine).
8. Allowed characters: plain Italian punctuation; no emoji, no markdown.

## Router records
- Telegraphic style: 2 to 4 words. Other styles follow the hint (formal, colloquial, broker, typo, code_mixed, etc.).
- Slots: write exactly what makes each slot present, missing or ambiguous as the hint says. If product is missing or ambiguous, do not mention the insurer either.
- **Contrastive pairs:** both members use the same topic, goal and wording; they differ only in the changed phrase, at most **8 words** in total. Pair members carry only typo or code_mixed modifiers.
- **History shape:** a list of turns `{"role":"user"|"assistant","text":"..."}` (no other keys).
- **History:** write the turns the scenario needs. `follow_up` and `slot_clarified` must have one exchange that introduces the coverage or field that is resolved from context; the assistant turn never states a figure. `resolved_slots` values must be consistent with the history and the job's `resolved_slot_keys`.
- **Leaked unsafe requests** (`leak_type`): state the intent only, in a different phrasing per held-out family; inject any unsafe part in at most **8 words**; do not give operational detail.
- **Client profiles:** use the profile in the hint; names are invented or initials.
- Comparison jobs: if a compared document is not in `available_docs`, say so with a skip only if the hint cannot be satisfied (planner defect, see G3).

## QA records
- Question types: single_value, conditional, multi_fact, absent. Difficulty as hinted.
- **Telegraphic QA** is the exception: the question has exactly **5 words**.
- Question must contain at least one distinctive term of the target chunk (guarantee name, figure label, section topic) so retrieval can find it. Avoid generic wording ("quanto è il limite?"). State the product.
- risposta: one or two sentences, a complete answer, includes the gold value and, for conditional, the condition. multi_fact answers cover every gold chunk.
- **Absent:** risposta is exactly `Non indicato nei documenti.`; fonte and gold_value are `null`; the question asks for a topic the documents do not cover (job `topic`/`angle`).
- Retrieval pre-check (bge, via the shared retrieval server the lead starts once): `write_batch.py` runs this retrieval pre-check itself (needs the shared server): an answerable QA is rejected with a `retrieval:` message if no gold chunk is in the bge top 5 (multi_fact: any gold chunk is enough). Do not run `qa_check.py` separately. If it says the server is not running, stop and report; never load a model yourself. On a `retrieval:` reject, reword the question (more distinctive terms), up to 3 tries; then skip. Report first-attempt hit@5 honestly.

## Complexity: make the label visible in the text (v2)
Each router record in the job shows a `>>` line with the exact requirement for its feature and complexity; follow it. The blind check read many "complex" records as simple because nothing in the text made them complex.
- **comparison simple:** 2 products, exactly 1 field, no criterion word. **comparison complex:** 2 products plus 2 or more fields (take them from `common_fields`) OR a criterion ("quale conviene", "meglio per un cliente che..."). One field for two products is simple, never complex.
- **regulatory simple:** one rule, one direct question. **regulatory complex:** two conditions or obligations that interact in one question (a date plus an exception, two named rules). A single-rule question is not complex, even if long.
- **product_policy_analysis complex:** combine 2+ chunks, a condition plus an exception, or a trade-off.
- **client_drafting / ibip_screening:** follow the label, but the text need not look complex (they route to agentic anyway). The job prints the client profile (`>> profile ...`); use its attributes.
- **Pairs that differ in complexity:** the 2 queries differ by at most 8 words; the complex member adds its trigger inside those words.
- Records with a missing or ambiguous slot are labelled as if complete: still write the complexity trigger, even when the slot is missing.
- The validator may print `warn:` lines for comparisons that look mislabelled; they do not reject the record, but rewrite the job if you agree.

## Diversity
Vary openings, length and vocabulary inside a batch; do not reuse the seed text. Seeds are style examples only.
