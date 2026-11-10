# 05. Evaluation protocol (shared by all systems)

Status: DRAFT v0.1. Read `00_overview_and_rationale.md` first (tags, checkpoint contract).

Every system (Kev zero-shot and fine-tuned, Nimble track if run, S1, S2-zero, S2-LoRA) is evaluated with this protocol so that numbers are comparable.

## 1. Inputs

- Calibration split and frozen hand-written test split from `01_data_spec_and_generation.md`.
- For each system, split and run: a file with **one line per (example, field)** containing the probability vector in **canonical label order** (not shuffled option order), the predicted label, the confidence, the gold label, and the time taken. `[OUR REQUIREMENT]`
- S1 and Kev produce their own confidences; map them to the same file format (see section 3).

## 2. Rules

1. **Test set discipline.** The test set is never used for training, prompt wording, thresholds, temperature, or checkpoint choice. Read it once per final candidate. This mirrors Kev's practice (choose with development sets, read each test set only once per released model). `[DOC: K-README, Benchmarks]` Nimble gives the same rule for its holdout. `[DOC: N-TRAIN]` `[OUR DECISION]` to adopt it.
2. **Thresholds and temperature** are fitted on the calibration split only. In-sample thresholds hide held-out misses: a paper found that thresholds chosen for a 5% miss target gave 95th-percentile held-out misses of 6 to 8% with 800 positives and 10 to 17% with 100 to 200 positives. `[DOC: P3 §6]`
3. **Same data, paired comparisons.** All systems are scored on identical test records. `[DOC: P3 §3]`
4. **Report hardware** for every latency number. `[OUR REQUIREMENT]`
5. **Costs are out of scope** (team decision); report latency, number of model calls, and escalation rate. `[OUR DECISION]`

## 3. Confidence definitions

`[OUR DECISION]`

- **Choice fields:** confidence = the maximum probability over options (after temperature scaling where applied). Kev's API also returns its own `confidence = (p_max - 1/K) / (1 - 1/K)`; this is a different quantity, so store both and say which one a number uses. `[DOC: K-README, API]` (A paper found that using a different "confidence" field than the max probability silently broke thresholds. `[DOC: P3 §3]`)
- **Slot questions:** probability that the slot is missing or ambiguous, `p_bad`; the decision is `p_bad >= t_slot` and the confidence is `max(p_bad, 1 - p_bad)`.
- **S1:** the probability of the label token in the generated JSON.
- **Overall confidence** for a request: the minimum over its fields (conservative).

## 4. Metrics

| Metric | Definition | Reported per |
|---|---|---|
| Accuracy | share of correct labels | field |
| Macro-F1 | mean of per-class F1 | field |
| Per-class recall | share of gold class found | field and class; **IBIP and client drafting always** |
| ECE | 15 equal-width confidence bins; weighted mean of the gap between accuracy and mean confidence in each bin (the papers use 15 bins `[DOC: P1 App. B, P2 §3.4]`) | field; before and after temperature scaling |
| Brier | mean over examples of the sum over classes of (probability - 1 if gold else 0) squared | field; before and after temperature scaling |
| Risk-coverage | for confidence threshold t: coverage = share of requests with confidence >= t; risk = error rate among them `[DOC: P4 §3.2]` | field |
| AURC | area under the risk-coverage curve `[DOC: P4 §3.2]` | field |
| Automatable share at an error budget | largest coverage whose error rate (threshold fitted on calibration) is at most the budget; Kev reports it at 5% `[DOC: K-README]` | field; budgets 5% and one stricter value to be agreed |
| Option-order change rate | share of answers that change when the option order changes `[DOC: P3 §5; K-README]` | field |
| Latency | p50, p95 and mean, in milliseconds | pipeline stage and end to end |

Note on Brier: papers define it differently (Kev says it scores the whole probability distribution `[DOC: K-README]`; other papers do not specify). Do not compare our values with published ones directly. `[OUR DECISION]`

Explain the metrics in the report in one line each (ECE: does confidence match reality; Brier: how far the whole probability vector is from the truth; pXX: the time under which XX% of requests finish).

## 5. Procedure

1. **Zero-shot runs** (no training): evaluate on calibration and test.
2. **Fit temperature** per field on calibration (grid search minimizing log loss). Where a system has its own stored temperature (Kev), report results with the stored and with the refitted one. `[DOC: K-README]` for the stored one.
3. **Fit thresholds** per field on calibration:
   - Choose the error target per field (open point; propose 5% as in Kev and the papers, and a stricter one for the sensitive features).
   - Use the risk-coverage curve to find the lowest threshold with error at most the target.
   - For slot decisions also fit `t_slot` by maximizing F1 on calibration (the Jev benchmark paper found that tuned per-question thresholds raised micro-F1 on a multi-label task from 0.50 to 0.75 against a fixed 0.5). `[DOC: P2 §4.3]`
4. **Test run:** apply the temperature and thresholds unchanged to the test set; report the metrics of section 4.
5. **Uncertainty:** report 95% confidence intervals from a paired bootstrap that resamples whole records, 2,000 resamples (Kev's practice) `[DOC: Kev-4B model card, seen only as a search snippet on a third-party mirror (haimaker.ai)]`, and use an exact McNemar test for paired accuracy differences between two systems `[DOC: P3 §3]`. State when a difference is within the noise (the Kev authors found a gain inside the noise at 400 records `[DOC: K-FT]`).
6. **Repeat with at least two seeds** for the final systems if time allows; single-seed differences of one to two points can be variance. `[DOC: P1 App. H]` `[OUR DECISION]`

## 6. Slices (always report)

`[OUR DECISION]`

- Italian-only requests; code-mixed or abbreviated phrasing.
- Contextual follow-ups and long contexts.
- Sensitive features (IBIP, client drafting): recall and, separately, the false-alarm rate.
- Contrastive pairs: **pair accuracy** (both members of a pair correct), since a model can be right on one member by guessing.
- Per cell of the generation grid (feature x complexity).
- Out-of-scope and quick-reply requests (false in-scope rate).

## 7. Robustness checks

- **Option order:** run each choice question with at least three orders (identity, reversed, one random) and report the answer-change rate. For Kev use `POST /v1/systemone/permute`. `[DOC: K-README, API]`
- **Prompt wording:** for S1 and S2, evaluate with at least three wordings of the instructions. A paper found that rewording changed per-track accuracy by 5 to 15 points for two systems, so single-wording numbers carry a band of roughly 5 points, while the ranking of systems was stable. `[DOC: P3 §5]` `[OUR DECISION]` on the number of wordings.
- **Precision:** state the dtype. For Kev, bf16 serving differs from the fp32 evaluation path by at most about 0.03 in probability and changes the top answer on about one question in 300. `[DOC: K-README, Serving Performance]`

## 8. Latency protocol

`[OUR DECISION]`

1. State GPU model, memory, dtype, library versions, batch size and whether the prefix or text is cached.
2. Warm up (a few requests discarded), then at least 200 requests of our real request shape: stage A (scope, feature, complexity) and stage B (slot questions of the predicted feature).
3. Measure model time and end-to-end client time separately (Kev's server returns `latency_ms` as model time; network time is extra `[DOC: K-README]`).
4. Report new-text vs repeated-text latency for Kev (its server caches the text). `[DOC: K-README]`
5. For S1, report tokens generated per request and time per generated token.
6. Free-tier GPU timings are not the demo hardware. If the demo hardware is known, repeat the measurement there (open point).
7. Reference numbers from the docs (different hardware, for orientation only): Kev-4B, six questions on short text: 18.1 ms on an H100, 41.5 ms on an L40S, about 721 ms for five questions on an Apple M5; Kev-0.8B 22.7 ms on an L4; Nimble 9B median 106 ms on an H100 and 444 ms on an M5 Pro. `[DOC: K-README, N-README]`

## 9. Fallback ladder evaluation

For each system with confidences: simulate the ladder on the test set using thresholds fitted on calibration:

1. confident answers are accepted;
2. below-threshold answers go to the next tier (a larger model, budgeted thinking, or the fail-safe route);
3. report accepted share, error among accepted, escalation rate per field, and the end-to-end latency of the accepted and escalated paths.

Consider the lesson from the agent-gating paper: report the **held-out** miss rate and the call rate, and count every component's calls. `[DOC: P3 §6, §9]` A cheap cascade with self-escalation (a small model asking itself whether to escalate) was competitive with a dedicated decision layer when routing was already accurate; S1 plays that role in our comparison. `[DOC: P4 §5.4]`

## 10. Report template

One table per field and one overall table:

| System | Data size | Accuracy | Macro-F1 | Sensitive recall | ECE raw | ECE cal. | Brier raw | Brier cal. | Automatable share at 5% | Order change | p50 ms | p95 ms | GPU |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Kev-0.8B zero-shot | | | | | | | | | | | | | |
| Kev-0.8B fine-tuned | | | | | | | | | | | | | |
| Kev-4B (if run) | | | | | | | | | | | | | |
| S2-zero (0.6B / 4B) | | | | | | | | | | | | | |
| S2-LoRA (0.6B / 4B) | | | | | | | | | | | | | |
| S1 zero-shot / LoRA | | | | | | | | | | | | | |
| Nimble track (if run) | | | | | | | | | | | | | |

Under the table: dataset hash, commit hashes, seeds, number of test reads, and the list of `[NOT DOCUMENTED]` findings that affected the run.

## 11. Decision rule (to be agreed)

`[OUR DECISION]` Proposal: choose the system that maximizes the automatable share at the agreed error budget, **subject to** sensitive-feature recall at least a target value, and p95 latency within the budget of the demo hardware. The targets (error budget, recall, latency) are open points: ask the mentor and the startup. Until they are set, report the full table without declaring a winner.

## 12. Checkpointing for evaluation jobs

`[OUR REQUIREMENT]` Write each prediction line as soon as it is computed to persistent storage; on restart, skip lines already present; keep `STATE.json` with counts per split and field; record the hardware at the start of the job.

## 13. Open points

1. Error budgets and the sensitive-feature recall target.
2. Demo hardware and latency budget.
3. Number of seeds and prompt wordings we can afford.
4. Whether to add a public benchmark (the Nimble repo documents a 13-subset public suite, `docs/PUBLIC_BENCHMARKS.md`, not read by the authors; System1-Arena, arXiv 2610.21244, not opened).
