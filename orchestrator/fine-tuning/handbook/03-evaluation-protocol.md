# 03 · Evaluation protocol (round 2)

The round-1 protocol (baselines chapters 05 and 06) is **unchanged**. This chapter lists what is new or fixed for fine-tuned runs. Where it is silent, baselines chapter 05 applies.

## Runs and references

| Fine-tuned run | Zero-shot reference run (round 1) |
|---|---|
| `laya-ft-multilingual-a` | `laya-multilingual-a` |
| `kev-0.8b-ft-a` | `kev-0.8b-20261112-a` |
| `kev-4b-ft-a` | `kev-4b-20261113-a` |

Logs go under `orchestrator/fine-tuning/runs/{laya,kev}/<run_id>/`. Kev-9B (`kev-9b-20261113-a`) is reference only: it is not fine-tuned.

Zero-shot values (route accuracy / macro-F1):

| | Validation | Test |
|---|---|---|
| Laya | 0.238 / 0.254 | 0.265 / 0.281 |
| Kev-0.8B | 0.349 / 0.357 | 0.331 / 0.329 |
| Kev-4B | 0.436 / 0.483 | 0.423 / 0.471 |
| Kev-9B (reference) | 0.473 / 0.534 | 0.567 / 0.617 |

Known weak spots to watch (round 1): clarification precision about 0.24; Kev-4B `lightweight` recall 0.044; prompt-injection refusal (Kev-4B 0.556 on 18 rows); Laya feature accuracy 0.337.

## Discipline (FT-C-14)

1. **Validation first.** Used for stopping, epoch choice, per-epoch metrics, and at most one second configuration.
2. **Test once per model**, after the configuration is frozen. No retry on test; a failed test run (infrastructure) is re-run identically, never with a changed configuration.
3. Harness: the round-1 runners with the small changes of chapter 07. 10 warm-up rows are excluded from latency (baselines P-03). The log validator (`common.logs.validate_log`) must report 0 errors and 0 error rows; the dispatcher oracle must match 593/593.

## Metrics

- **Primary:** route accuracy and route macro-F1.
- **Secondary:** scope, feature and complexity accuracy; `needs_clarification` precision and recall; `lightweight` recall; refuse recall overall, on the safety-leak slice (35 test rows) and on prompt injection (18 test rows).
- **Carried over from round 1 (FT-C-16):** per-class precision/recall/F1 and macro-F1 per output, the per-route breakdown, the "first wrong field" attribution table, tokens (`input_tokens_native`, `input_tokens_ref`), latency, model size (parameters, disk, peak GPU memory).
- **ECE (FT-C-15):** reported **both** raw (temperature 1) and calibrated (the fitted temperature), side by side, per question, as in round 1 (10 equal-width bins on `p_max`, baselines L-02c). The raw and calibrated distributions must both be reproducible from the log: store the fitted temperature in `run.json` and log `temperature_applied`; if the runtime only returns calibrated probabilities, store logits so raw can be recomputed (baselines chapter 06 rule on logits).
- **Do not add other metrics.** Baselines C-20 still holds.

## Comparison with zero-shot (FT-C-14)

For each model the comparison table shows, for the same `query_id`s: zero-shot, fine-tuned, and the difference, for the primary and secondary metrics. For route accuracy and route macro-F1 it adds the **paired-bootstrap 95% interval** of the difference (FT-P-04).

- **No decision rule.** The report shows the intervals and states them; it does not declare a "gain" or "no gain" by a threshold, and it does not require scope or feature accuracy to stay at or above zero-shot. A reader draws the conclusion.
- No winner is named on gaps inside noise (baselines chapter 05). Comparisons with another model (for example fine-tuned Kev-0.8B against zero-shot Kev-4B) are labelled **context, not a like-for-like gain**.
- The bootstrap code goes in `common/compare.py` style and is tested on a synthetic log with a known difference and on two identical logs (interval contains zero).

## Comparability of latency and size

Latency and tokens are comparable with the zero-shot runs only on the same hardware, dtype and path:

| Model | Evaluate on |
|---|---|
| Laya | Kaggle T4, fp16 (as `laya-multilingual-a`). Fine-tuned weights are saved as fp16 by `save_checkpoint`. |
| Kev-0.8B | Kaggle T4, fp32, in-process (as `kev-0.8b-20261112-a`), `causal_conv1d` fallback path. |
| Kev-4B | Kaggle T4, bf16, in-process (as `kev-4b-20261113-a`), `causal_conv1d` fallback path. |

Any deviation is labelled in the report. Peak GPU memory during **training** is recorded separately in `train_report.json`; it is not part of the evaluation table.

## Report layout per run

`report.md` and `metrics.json` from the shared script, plus:

1. Run header: base model and revision, `finetuned_from`, `train_run_id`, hyperparameters, dtype, GPU, library versions, number of training and calibration records, fitted temperature(s), sha256 of the checkpoint.
2. The comparison table above.
3. A short list of **what moved and what did not** (per route, per slice), without verdict language.
4. Training curve summary from `epochs.jsonl` (development route macro-F1 per epoch for Laya).

A cross-pipeline `comparison.md` (shared script, tolerant of missing runs) puts the three fine-tuned runs next to their zero-shot references and flags any non-comparable row.
