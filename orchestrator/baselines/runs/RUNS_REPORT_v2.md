# Orchestrator baselines, round 2 (v2 protocol): run report and comparison

Snapshot 13 Nov 2026. Companion to `RUNS_REPORT.md` (round 1, v1 protocol), which stays as written. Round 2 re-runs **Kev-0.8B** and **Laya** zero-shot on the v2 dataset and question set. Nimble was dropped (C-34).

Numbers come from `runs/<pipeline>/<run_id>/metrics_{test,validation}.json`, `report_*.md` and `run.json`. The Kev v2 report files were generated for this document with `kev/make_report.py` (they did not exist before); the Laya v2 reports were already there. Same hardware (Kaggle T4, two GPUs visible), same splits (test 593 rows, validation 298), 0 error rows, 0 truncated, and the dispatcher oracle matches 593/593 on both v2 runs.

**Do not rank on small gaps.** One run each, one question wording (`questions.en.yaml`, state template p-01).

## 0. What changed from v1 to v2 (read this first)

| | v1 | v2 |
|---|---|---|
| Routes | 5: lightweight, agentic, **clarification**, refuse, quick_reply | 4: no clarification route |
| Questions per row | core (scope, feature, complexity, needs_clarification) + slot questions of the predicted feature, **two model calls** | scope, feature, complexity only, **one call**, no slots |
| Question config sha256 | `193e1c62...` | `eb2cfd38...` |
| Test gold routes | lightweight 183, agentic 159, clarification 102, refuse 95, quick_reply 54 | lightweight 201, agentic 243, refuse 95, quick_reply 54 |
| Data manifest (test) | `c1bbc865...` | `24253ef5...` |

**Checked on the logs:** for both models, the scope, feature and complexity labels on all 593 test rows are identical between v1 and v2 (0 rows differ per question). The v2 runs did not change what either model predicts for those three questions. So:

- scope / feature / complexity accuracy, macro-F1, ECE and refusal recall are the **same numbers as v1**, not new results.
- What is new is the **route** (4-way, no clarification, 102 gold clarification rows redistributed to lightweight/agentic) and the **cost** (one call instead of two).
- A v1 to v2 jump in route accuracy comes from dropping the weakest question (needs_clarification) and its route. It is **not** a model improvement, and the two route numbers are not comparable like for like (different label sets).

## 1. How each v2 run went

| | Kev-0.8B v2 | Laya v2 |
|---|---|---|
| Run id | `kev-0.8b-v2-20261113-a` | `laya-v2-a` |
| dtype / hardware | float32, 1 x T4 | fp16, 1 x T4 |
| Parameters | 0.75B | 0.32B |
| Disk (MB) | 1835 (adapter 65.5 + base 1769.9) | 678 |
| Peak GPU | 3.2 GB | 1.5 GB |
| Load time | 7.6 s | 8.1 s |
| Wall time, val + test | ~4.6 min (v1: ~7) | ~33 s (v1: ~1 min) |
| Revision | `9a45d25e` (the model card's weights revision) | `85cc74dd` (same as v1) |
| Temperature | 2.351 (same as v1, calibrated on the v1 task) | applied internally, not reported |
| Weights sha256 | `9b908623...` (same as v1) | n/a |

Notes:
- Kev v2 loaded revision `9a45d25e` directly; v1 loaded `bf75a6a8` (the `main` commit). The adapter hashes are identical across both, so the weights are the same.
- Kev v2 `disk_mb_base` is 1769.9 here against 1746.9 in the hand-corrected v1 `run.json`. Different recording; the model files are the same. Peak GPU (3217.3 MB) is identical to v1 to the decimal, which fits a deterministic run but was not investigated.
- The Kev v2 temperature was fitted for the v1 question set. It was reused unchanged; the identical probabilities/labels above are consistent with that, but it has not been re-calibrated for v2.
- Pilot (50 val rows) and smoke (5 rows) folders exist for Laya v2, and a smoke folder for Kev v2. They are checks, not results.

## 2. v2 only: the two models tested on v2 (test split, 593 rows)

| Metric | Kev-0.8B v2 | Laya v2 |
|---|---|---|
| scope_check accuracy / macro-F1 | **0.788** / **0.553** | 0.649 / 0.546 |
| feature accuracy / macro-F1 | **0.663** / **0.693** | 0.337 / 0.349 |
| complexity accuracy / macro-F1 | **0.727** / **0.726** | 0.523 / 0.378 |
| **route accuracy** (4 routes) | **0.654** | 0.415 |
| **route macro-F1** | **0.550** | 0.421 |
| refuse recall (all 95) | 0.126 | **0.411** |
| refuse recall, safety-leak (35) | 0.057 | **0.571** |
| refuse recall, prompt injection (18) | 0.000 | **0.389** |
| refuse precision | **0.923** | 0.255 |
| ECE scope / feature / complexity | 0.271 / **0.181** / **0.107** | **0.117** / 0.409 / 0.326 |
| mean latency (ms) | 286 | **32.5** |
| native input tokens (mean) | **381** | 551 |
| reference-tokenizer input tokens (mean) | 389 | 389 |
| parameters / peak GPU | 0.75B / 3.2 GB | **0.32B / 1.5 GB** |

Bold marks the best value in the row. Output tokens were not recorded.

### Per-route precision / recall (test, v2)

| Route (support) | Kev-0.8B v2 | Laya v2 |
|---|---|---|
| lightweight (201) | 0.64 / 0.70 | 0.45 / 0.59 |
| agentic (243) | 0.74 / 0.80 | 0.53 / 0.21 |
| refuse (95) | 0.92 / 0.13 | 0.26 / 0.41 |
| quick_reply (54) | 0.42 / 0.76 | 0.47 / 0.69 |

### Where wrong routes first go wrong (test, v2)

| First wrong field | Kev-0.8B v2 | Laya v2 |
|---|---|---|
| scope_check | 126 | 208 |
| feature_classification | 49 | 120 |
| complexity_estimation | 30 | 19 |
| **total wrong routes** | 205 | 347 |

### Validation split (298 rows)

| Metric | Kev-0.8B v2 | Laya v2 |
|---|---|---|
| scope accuracy | 0.799 | 0.614 |
| feature accuracy | 0.664 | 0.406 |
| complexity accuracy | 0.772 | 0.522 |
| route accuracy | 0.678 | 0.393 |
| route macro-F1 | 0.596 | 0.395 |
| refuse recall | 0.208 | 0.292 |
| mean latency (ms) | 277 | 32.4 |

### What v2 shows for these two models

1. **Kev-0.8B is clearly ahead of Laya on route quality** (0.654 vs 0.415 test accuracy, 0.678 vs 0.393 on validation). It wins on scope, feature, complexity and route macro-F1, and its `agentic` recall is 0.80 against 0.21.
2. **The remaining Kev error is the scope gate.** 126 of its 205 wrong routes go wrong at `scope_check`, because it almost never refuses (recall 0.126 on test, 0.057 on safety leaks) even though refuse precision is 0.92. Laya refuses more often but with 0.26 precision.
3. **Laya is still the cheap option** (32 ms, 1.5 GB, 0.32B), but it predicts `simple` for 96.5% of in-scope complexity rows (complex recall 0.042) and its feature accuracy is 0.337.
4. **One call per row roughly halves cost** for both: Kev 431 to 286 ms, Laya 58 to 32.5 ms mean latency, and Kev native input tokens 552 to 381. The latency caveats of round 1 still apply: fp32 vs fp16, Kev on the `causal_conv1d` fallback path.

## 3. All runs together: v1 and v2 side by side (test split)

Columns: the two models that have a v2 run, in their v1 run (from `RUNS_REPORT.md`) and in their v2 run. For a model run in both rounds, the three core-question rows are identical by construction (section 0).

| Metric | Kev-0.8B v1 | Laya v1 | Kev-0.8B v2 | Laya v2 |
|---|---|---|---|---|
| Routes / calls per row | 5 / 2 | 5 / 2 | 4 / 1 | 4 / 1 |
| scope_check accuracy | 0.788 | 0.649 | 0.788 | 0.649 |
| feature accuracy | 0.663 | 0.337 | 0.663 | 0.337 |
| complexity accuracy | 0.727 | 0.523 | 0.727 | 0.523 |
| needs_clarification accuracy | 0.423 | 0.360 | not asked | not asked |
| route accuracy | 0.331 | 0.265 | **0.654** | 0.415 |
| route macro-F1 | 0.329 | 0.281 | 0.550 | 0.421 |
| refuse recall (all 95) | 0.126 | 0.411 | 0.126 | 0.411 |
| refuse recall, safety-leak (35) | 0.057 | 0.571 | 0.057 | 0.571 |
| ECE scope | 0.271 | 0.117 | 0.271 | 0.117 |
| ECE feature | 0.181 | 0.409 | 0.181 | 0.409 |
| mean latency (ms) | 431 | 58 | 286 | **32.5** |
| native input tokens (mean) | 552 | 883 | 381 | 551 |
| parameters | 0.75B | 0.32B | 0.75B | **0.32B** |
| peak GPU | 3.2 GB | 1.5 GB | 3.2 GB | **1.5 GB** |

Route accuracy and route macro-F1 for v1 and v2 columns use **different route label sets and gold data** (v1: 5 routes including clarification; v2: 4). Compare them within a round, not across.

### Findings across both rounds

1. **Removing clarification is what lifts route accuracy, not a better model.** Kev-0.8B goes from 0.331 (v1) to 0.654 (v2) and Laya from 0.265 to 0.415 with the same predictions. In v1, `needs_clarification` was the first wrong field for 191 of Kev-0.8B's 397 wrong routes and 73 of Laya's 436. The v2 design removes that failure source (accuracy on that question was 0.42 for Kev-0.8B and 0.36 for Laya).
2. **Within v2, Kev-0.8B > Laya on quality, as in v1.** Laya remains about 9 times faster than Kev-0.8B (32.5 vs 286 ms) and smaller in memory.
3. **Refusal is unchanged by the protocol and is the main gap for Kev-0.8B** (recall 0.126). Scope_check causes 126 of its 205 wrong routes, so better refusal would probably help most.
4. **Cost drop is real and protocol-driven:** one call per row, 34% (Kev) and 44% (Laya) lower mean latency and, for Kev, 31% fewer input tokens.

## 4. Caveats that must travel with these numbers

- **v2 re-uses v1 predictions.** The v2 core-question metrics are not independent replications; they are the same outputs, so they add no information about run-to-run variance. There is still no variance estimate and no sensitivity to prompt wording.
- **Route metrics are not comparable across v1 and v2** (different label sets, different gold data, section 0).
- **Only two models have a v2 run.** Round 2 covers these two models only (Nimble was dropped, C-34). X-04 (confidence definition) is still pending.
- **Temperature for Kev v2 is the v1 value** (2.351), not re-fitted for the v2 question set. Laya applies its own temperatures internally and does not report them.
- **Latency is not comparable across dtypes** (fp32 Kev vs fp16 Laya) and Kev runs on the `causal_conv1d` fallback path (label as "fallback path", C-32).
- **Refusal numbers are noisy.** Prompt injection is 18 test rows, and validation and test differ (Kev-0.8B refuse recall 0.208 vs 0.126).
- **Version control:** the v2 run folders (`runs/kev/kev-0.8b-v2-*`, `runs/laya/laya-v2-*`) are untracked in git at the time of writing.
- **Run-folder hygiene:** the Kev v2 `report_*.md`, `metrics_*.json` and confusion CSVs were produced after the run, locally, by `make_report.py` from the committed log files; the logs themselves were not modified.

## 5. Next steps

1. Decide whether to re-fit the Kev temperature for the v2 question set before further Kev v2 runs.
2. Commit the v2 run folders and the generated reports.
3. Resolve X-04 (confidence definition).
4. Install `causal_conv1d` (or accept the label) before any latency comparison.

## Sources

`runs/kev/kev-0.8b-v2-20261113-a`, `runs/laya/laya-v2-a` (`run.json`, `metrics_*.json`, `report_*.md`); round-1 runs `runs/kev/kev-0.8b-20261112-a`, `runs/laya/laya-multilingual-a` as summarised in `RUNS_REPORT.md`; row-level v1 vs v2 label comparison computed from the `test.jsonl` logs.
