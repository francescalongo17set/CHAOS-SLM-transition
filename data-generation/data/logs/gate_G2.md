# Gate G2 report (after stage 5)

auto_approved: true (draft mode, book section 13). Human decisions deferred: seed approval, deviations above 5%.

## Delivered
seeds/seeds.jsonl (230 seeds), seeds/client_profiles.jsonl (300), plan/jobs.jsonl, plan/STATE.json, plan/compatibility_matrix.csv, plan/plan_assertions.md.

## Planned counts against the quotas
All planned counts equal sections 5, 6, 7.1, 8 and 9: cells x routes x splits, the five route totals, the source table, scenarios, modifiers, styles, pairs, and Dataset 2 per type, document and split (1,500 QA: 850/150/500). The matrix margins equal the book counts by construction (integer programming), and plan_assertions.md shows 69 of 69 checks passing.

## Capacity ladder (book 16.3), recorded in plan/STATE.json
| Document, split | Level reached | QA cap | Why |
| --- | --- | ---: | --- |
| Zurich Salute, train | step 3 | 5 | 59 value chunks and the 20% section cap (64 of 320 per section) |
| Generali, train | step 1 | 3 | 100% of capacity at the base cap |
| Zurich Salute, validation | step 2 | 4 | 13 value chunks for 49 questions |
| Generali, validation | step 2 | 4 | only 6 chunks have both a value and a condition, for 19 conditional questions |
| Zurich Impresa, test | step 1 | 2 | 100% of capacity at the base cap |
Step 4 (moving questions to the other document) was not needed. No Dataset 2 quota was reduced. Absent quotas are met with 5 questions per topic at most.

## Interpretations and deviations (the book is silent or contradictory)
1. **Family key.** Salute, Generali and Italiana R&I+ feed both train and validation, so a family equal to the product would break "no family in two splits". Validation families carry the suffix `__heldout` (for example `zurich_salute__heldout`); comparison families join the two parts. Leak phrasing families are the seed lineage; the held-out ones are in validation or test only.
2. **Insurer slot.** When the product is missing or ambiguous, insurer is dropped from required_slots, filled_slots and slot_status, so exactly one slot is non-present and missing_info lists only product.
3. **Telegraphic.** Router queries use 2 to 4 words, but the QA question bound is 5 to 40 words. QA telegraphic questions therefore use 5 words (product and coverage named, no verb). The writer card must say so.
4. **Section spread.** The 20% cap (80 for Impresa) counts answerable questions, which have a source section. Absent questions have none. Counting them made Salute train unsatisfiable. Validation is one held-out section and is exempt.
5. **Context conflict** is planned for train and validation only (120: 104 + 16). The book requires two chunked documents in the split and test has one.
6. **Pairs.** Pair members share one style and may carry only typos or code-mixed modifiers (no preamble, telegraphic, mixed features, innocent imperative, negation or conflict), so the 8-word limit is reachable. Pair types as built: missing_info = clarification record plus its complete version; complexity = PA simple lightweight plus comparison complex agentic; feature = PA simple lightweight plus client drafting agentic (same product); leaked = valid request (PA or regulatory) plus its injected version, and 36 borderline unsafe requests plus a legitimate regulatory sibling. In the leaked pairs the injected part must stay within 8 words. Context-flip pairs were not built.
7. **Comparisons** use two chunks (one per product) and a field from comparable_fields.csv; complex ones are chosen with two or more shared fields when possible. Three-product comparisons are not possible with two chunked documents per split. At most 6 comparison records per (field, coverage pair) per split; router-only uses stay within 3 per chunk (2 in test).
8. **Borderline leaks.** Only 5 of the 50 seeds are borderline; the planner assigns 36 borderline records (16 fraud, 10 data extraction, 6 social engineering, 2 jailbreak, 2 injection), each in a pair with a legitimate sibling. Validation and test leaks come from one seed each per type, so the writer must vary the phrasing a lot (no template more than 5 times).
9. **Quick replies** have 3 seed families per type: one each for train, validation and test.
10. **IBIP test.** Test uses the 3 Allianz seed families only (74 records).
11. **Drafting records in validation** carry the product name but no Assistance-specific topic.
12. **Hard negatives** are only planned here (480, 40% of answerable QA); stage 8 verifies them against the real top 5.
13. History for follow-up router records uses a chunk of the same document and pool from a different section; context-conflict records use the other document. Test windows use Impresa chunks only.

## Open risks
- The held-out leak phrasing in validation (18) and test (36) comes from very few seeds.
- Many Salute train questions reuse chunks up to 5 times: the writer must return skip lines when a chunk has no further distinct fact (fact_index in each job tells which fact to take). Skips are replaced by the planner.
- The validator needs the written word-count bounds, the 8-word pair rule and the telegraphic QA exception.

## Decisions a human would take (deferred)
Seed approval (230); whether to keep the 5-use cap for Salute train; context-flip pairs; larger seed families for the held-out leaks.
