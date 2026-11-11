# Gate G1 report (after stage 3)

auto_approved: true (draft mode, book section 13). The human decisions in the last column of the gate table are deferred.

## Delivered
- chunks/chunk_report.md: counts, sizes, coverage, held-out sections, 20 random chunks per document in full.
- catalogue/field_lexicon.yaml, absent_candidates.csv, comparable_fields.csv, chunk_catalogue.jsonl, catalogue_summary.md.

## Checks against the acceptance criteria (book 13 and 15)
| Check | Result |
| --- | --- |
| Page counts | 53 / 140 / 188: pass |
| Pages without text layer | Generali 3 of 140 (2.1%), others 0: pass (limit 5%) |
| Chunk counts within 30% of estimate | -4% / 0% / -5%: pass |
| Chunk size 300 to 2,400 chars | pass |
| Coverage at least 98% | 99.2 / 99.6 / 99.5%: pass |
| Held-out sections found and unambiguous | Salute p34-42 (32 chunks), Generali p35-53 (52 chunks): pass |
| Forbidden characters | none |
| Comparable fields 8 / 4 / 8 | 14 / 5 / 14: pass |

## Deviations (all logged, none above the stop limits)
1. Margin rule extended: lines repeating on 10 or more pages are removed as well (stage 1).
2. A chunk also closes before a sub-heading once it has 600+ characters; short leading chunks merge forward (stage 2).
3. single_value no longer requires exactly one field (stage 3). Reason: the strict test left 9 usable Salute train chunks for 128 questions.
4. 11 Generali outline entries were not found on their page and are placed at the top of the page (4% of headings).

## Capacity findings for the planner (book 16.3)
| Document and pool | Value chunks | Demand | Ladder step |
| --- | ---: | ---: | --- |
| Salute train | 59 | 208 | step 2, QA cap 4 |
| Salute validation (Assistance) | 13 | 49 | step 2, QA cap 4 (94% of capacity) |
| Generali train | 145 | 344 | step 1, 100% at base cap |
| Generali validation | 42 | 49 | none |
| Impresa test | 165 | 325 | step 1, 100% at base cap (98%) |

Absent topics: usable topics x 5 questions give Salute train 125 (quota 64), Generali train 135 (106), Salute validation 55 (15), Generali validation 50 (15), Impresa test 105 (100). Impresa is tight: 20 of 21 topics must give 5 questions each.

## Open risks
- Absent topics are keyword zero-hits, unconfirmed. Some may be stated under other wording or on a page the extractor read badly.
- The DIP and DIP aggiuntivo front pages summarise the held-out sections and stay in the train pool (open point of section 12).
- Impresa DIP aggiuntivo is 168 of 536 chunks (heavy tables with very long cells); the 80-questions-per-section spread cap applies to it.
- Heading paths in DIP/DIPA pages are less precise than in the conditions (font-based bold rule).

## Decisions a human would take (deferred)
Chunks readable and held-out sections right; second reviewer confirms the absent topics; size of the comparison cell (not an issue: enough fields).
