# Orchestrator baselines, round 1: run report and comparison

Snapshot 13 Nov 2026. Three open decision models (Kev, Laya, Nimble) run **zero-shot** on the Italian router dataset. Nimble is **not run** (blocked on owner decision X-05, quantization). X-04 (confidence definition) is also pending.

All numbers below come from `runs/<pipeline>/<run_id>/metrics_{test,validation}.json` and `run.json`. Each run is a single run with one question wording (`questions.en.yaml`, state template p-01) on a Kaggle T4 (two GPUs visible). Test is 593 rows, validation 298 rows. Every log passes `common.logs.validate_log` (0 errors, 0 error rows), and the dispatcher oracle (gold fields mapped to routes) matches 593/593 on every run.

**Do not rank on small gaps** (chapter 05). With one run each, differences of a few points are within noise; the split-to-split movement below (for example Kev-4B refuse recall 0.94 on validation vs 0.79 on test) shows how large that noise can be.

## 1. How each run went

| | Kev-0.8B | Kev-4B | Kev-9B | Laya |
|---|---|---|---|---|
| Run id | `kev-0.8b-20261112-a` | `kev-4b-20261113-a` | `kev-9b-20261113-a` | `laya-multilingual-a` |
| Date | 12 Nov | 13 Nov | 13 Nov | 13 Nov |
| dtype | float32 | bfloat16 | bfloat16 | fp16 |
| Hardware layout | 1 x T4 | 1 x T4 | 2 x T4, layer split (own loader, C-33) | 1 x T4 |
| Parameters | 0.75B | 4.21B | 7.94B | 0.32B |
| Disk (MB) | 1812 (adapter 65.5 + base 1747) | 159.7 (adapter only) | 201.7 (adapter only) | 678 |
| Peak GPU | 3.2 GB | 8.9 GB | 16.3 GB (13.6 + 2.7) | 1.5 GB |
| Load time | 8 s (warm cache) | 8.7 s (warm) | 116 s | 8 s |
| Wall time, val + test | ~7 min | ~54 min | ~87 min | ~1 min |
| Revision | `bf75a6a8` (Hub tag v1.0) | `139fdd94` | `b5d8c18e` | `85cc74dd` |
| Temperature | 2.351 (shipped) | 2.406 (shipped) | 2.194 (shipped) | not reported (applied internally) |

### Kev-0.8B (`kev-0.8b-20261112-a`)
- Ran the fp32 eager path, the exact path the model was built for. The first request of the process took about 102 s (kernel compilation) and was absorbed by the 10 warm-up rows.
- `causal_conv1d` is not installed, so Transformers used its slower PyTorch fallback. Latency reflects that path.
- The Hub tag `v1.0` moves. The run loaded commit `bf75a6a8`. A check on 13 Nov showed the adapter and head hashes are identical to the model card's weights revision `9a45d25e`, so the weights are the card's.
- `run.py` recorded only the adapter size; the base disk size and `weights_sha256` were added to `run.json` by hand.
- Outcome: weakest Kev. Almost no refusal (recall 0.126; safety-leak 0.057).

### Kev-4B (`kev-4b-20261113-a`)
- Loaded in bf16 (decision C-32), not the fp32 exact path, because of GPU memory. A T4 has no native bf16, which, together with the `causal_conv1d` fallback, makes it about 8x slower than the 0.8B run.
- Adapter sha256 matches the model card. Disk size is adapter only (`disk_mb_base` null).
- Outcome: refusal recovers (recall 0.789) but `lightweight` is almost never predicted (recall 0.044) and clarification is over-flagged.

### Kev-9B (`kev-9b-20261113-a`)
- Does not fit one T4 in bf16, so it was split across 2 x T4 with our own loader (`kev/shard.py`, decision C-33): layers 0-25 on GPU 0, 26-31 on GPU 1, LoRA merged on CPU. This loader is not covered by upstream tests. Cross-GPU copies add to latency.
- Smoke run (5 rows) passed first; load took 208 s cold and 116 s in the full run.
- `run.json` shows `model_revision` as the same hash twice (cosmetic; the hash equals the pinned revision). `disk_mb_base` is null. Peak GPU is the sum of two devices.
- Outcome: best Kev on every route-level number, still far from usable.

### Laya (`laya-multilingual-a`)
- Runs as a small encoder with a decision head (0.32B). fp16, 1 x T4, about 1 minute for both splits. Laya applies its own temperatures inside `predict()` and does not report them, so `temperature_applied` is null and the probabilities are as shipped.
- Library versions differ from Kev's (torch 2.11, transformers 5.20.2, laya 0.4.31).
- Pilot (50 val rows) and smoke (5 rows) runs exist as small checks only, not results.
- Outcome: by far the fastest, but the weakest on every quality metric except scope calibration.

Shared across all runs: two model calls per row (core questions, then slots of the predicted feature, C-23); tokens and latency are summed over both. The 10 warm-up rows are excluded from latency (583 rows counted on test). Ground truth is `router.jsonl`, with no relabeling and no training or tuning on any split.

## 2. Comparison (test split, 593 rows)

| Metric | Kev-0.8B (fp32) | Kev-4B (bf16) | Kev-9B (bf16, 2 GPU) | Laya (fp16) |
|---|---|---|---|---|
| scope_check accuracy | 0.788 | 0.801 | **0.855** | 0.649 |
| scope_check macro-F1 | 0.553 | 0.773 | **0.822** | 0.546 |
| feature accuracy | 0.663 | 0.801 | **0.815** | 0.337 |
| feature macro-F1 | 0.693 | 0.810 | **0.831** | 0.349 |
| complexity accuracy | 0.727 | 0.822 | **0.836** | 0.523 |
| needs_clarification accuracy | 0.423 | 0.383 | **0.559** | 0.360 |
| needs_clarification precision / recall | 0.234 / 0.667 | 0.233 / 0.735 | 0.294 / 0.657 | 0.239 / 0.814 |
| **route accuracy** | 0.331 | 0.423 | **0.567** | 0.265 |
| **route macro-F1** | 0.329 | 0.471 | **0.617** | 0.281 |
| refuse recall (all 95) | 0.126 | **0.789** | 0.779 | 0.411 |
| refuse recall, safety-leak (35) | 0.057 | **0.771** | 0.629 | 0.571 |
| refuse recall, prompt injection (18) | 0.000 | **0.556** | 0.333 | 0.389 |
| ECE, scope_check | 0.271 | 0.150 | 0.137 | **0.117** |
| ECE, feature | 0.181 | 0.197 | **0.112** | 0.409 |
| mean latency (ms) | 431 | 3639 | 5669 | **58** |
| native input tokens (mean) | 552 | 605 | 589 | 883 |
| reference-tokenizer input tokens (mean) | 518 | 560 | 547 | 556 |
| parameters | 0.75B | 4.21B | 7.94B | **0.32B** |
| peak GPU | 3.2 GB | 8.9 GB | 16.3 GB | **1.5 GB** |

Bold marks the best value in the row. Output tokens were not recorded for any run (`output_native` n = 0).

### Per-route precision / recall (test)

| Route (support) | Kev-0.8B | Kev-4B | Kev-9B | Laya |
|---|---|---|---|---|
| lightweight (183) | 0.48 / 0.31 | 0.80 / 0.04 | 0.83 / 0.34 | 0.40 / 0.10 |
| agentic (159) | 0.31 / 0.12 | 0.64 / 0.36 | 0.71 / 0.55 | 0.39 / 0.06 |
| clarification (102) | 0.22 / 0.66 | 0.24 / 0.66 | 0.31 / 0.65 | 0.18 / 0.52 |
| refuse (95) | 0.92 / 0.13 | 0.44 / 0.79 | 0.54 / 0.78 | 0.25 / 0.41 |
| quick_reply (54) | 0.42 / 0.76 | 1.00 / 0.80 | 1.00 / 0.85 | 0.47 / 0.69 |

### Where wrong routes first go wrong (test)

| First wrong field | Kev-0.8B | Kev-4B | Kev-9B | Laya |
|---|---|---|---|---|
| needs_clarification | 191 | 183 | 138 | 73 |
| scope_check | 126 | 118 | 86 | 208 |
| feature_classification | 80 | 40 | 30 | 153 |
| complexity_estimation | 0 | 1 | 3 | 2 |
| **total wrong routes** | 397 | 342 | 257 | 436 |

### Validation split (298 rows), for reference

| Metric | Kev-0.8B | Kev-4B | Kev-9B | Laya |
|---|---|---|---|---|
| scope accuracy | 0.799 | 0.792 | 0.842 | 0.614 |
| feature accuracy | 0.664 | 0.775 | 0.832 | 0.406 |
| complexity accuracy | 0.772 | 0.812 | 0.804 | 0.522 |
| needs_clarification accuracy | 0.415 | 0.384 | 0.460 | 0.308 |
| route accuracy | 0.349 | 0.436 | 0.473 | 0.238 |
| route macro-F1 | 0.357 | 0.483 | 0.534 | 0.254 |
| refuse recall | 0.208 | 0.938 | 0.854 | 0.292 |
| mean latency (ms) | 430 | 3591 | 5701 | 58 |

## 3. Findings

1. **Kev-9B is ahead on route quality.** Route accuracy 0.567 vs 0.423 (4B), 0.331 (0.8B) and 0.265 (Laya), and it leads on scope, feature, complexity and needs_clarification accuracy. The order 9B > 4B > 0.8B holds on both splits for route macro-F1, but the gap between 4B and 9B on validation (0.436 vs 0.473 accuracy) is small. Treat 9B > 4B as likely, not established.
2. **No model is usable as a router yet.** The best route accuracy is 0.567, and every model scores 0.31 precision or lower on clarification.
3. **`needs_clarification` is the dominant error source for all Kev sizes** (191 / 183 / 138 first-wrong routes). Kev over-flags clarification: precision 0.23 to 0.31 against recall 0.65 to 0.74. Laya over-flags it too (recall 0.814, precision 0.239) but its errors concentrate earlier, at scope and feature.
4. **`lightweight` is badly under-predicted** by 4B (recall 0.044) and 9B (0.344), with high precision. The models seem to send those requests to clarification or agentic instead.
5. **Refusal depends on size within Kev, and prompt injection is the weak spot.** Recall goes 0.126 (0.8B) to 0.789 (4B) and 0.779 (9B). Prompt injection (18 test rows) is 0.000 / 0.556 / 0.333 for the three Kev sizes and 0.389 for Laya. Note the 9B safety-leak recall (0.629) is below the 4B (0.771), and 4B refuse recall moved from 0.938 (validation) to 0.789 (test), so refusal numbers are noisy.
6. **Laya is the cheap and fast option but not competitive on quality.** 58 ms, 1.5 GB and 0.32B parameters, but feature accuracy is 0.337 and complexity recall for `complex` is 0.042 (it predicts `simple` almost always). Its scope_check ECE (0.117) is the lowest of the four despite the lowest accuracy, which says little more than that its scope probabilities are not overconfident; its feature and complexity calibration is the worst (ECE 0.409 and 0.326).
7. **Calibration improves with Kev size** on feature, complexity and slots (9B ECE 0.112 / 0.069 / 0.116 vs 0.8B 0.181 / 0.107 / 0.275). The 4B is not better than the 0.8B on feature ECE (0.197 vs 0.181).
8. **Token use is similar across Kev sizes** (552 to 605 native input tokens). Laya's native count (883) is higher because it uses its own tokenizer; on the shared reference tokenizer all four sit at 518 to 560.

## 4. Caveats that must travel with these numbers

- **Latency is not comparable across Kev sizes or against Laya.** Different dtypes (fp32 / bf16 / fp16), bf16 on a T4 without native bf16, the 9B split over two GPUs with cross-device copies, and all Kev runs on the `causal_conv1d` fallback path. Label the dtype in any table (C-32). The default, until the owner decides otherwise, is to label all Kev latencies as "fallback path".
- **The dtype mix is real:** 0.8B is the exact fp32 path, 4B and 9B are bf16 approximations, so part of the size effect could be a precision effect.
- **Single run, one question wording**, so no variance estimate and no sensitivity to prompt wording.
- Kev-9B peak GPU is the sum over two devices. The split loader is our own code (C-33).
- Laya's temperatures are applied internally and not reported, so its probabilities cannot be compared on temperature grounds, and confidence work (X-04) would need a decision there.
- Minor logging issues: Kev-0.8B `run.json` disk sizes and `weights_sha256` were corrected by hand; Kev-4B/9B `disk_mb_base` is null; Kev-9B `model_revision` shows the hash twice. Kev GitHub release checksums for the adapters were not checked (Hub hashes only).
- Nimble is missing, so this is not yet the three-way comparison round 1 asks for.

## 5. Next steps

1. Owner decides X-05 (and X-04), then write the Nimble plan (chapters 10 and 11) before any code.
2. Open the PR for the Kev-9B branch (`orchestrator/baselines-kev-9b`) into `orchestrator/baselines`; the run folders and doc updates are committed there but the PR is still to open.
3. Install `causal_conv1d` (or accept the label) before any latency comparison between sizes.
4. P4: run `common/compare.py` once Nimble exists. It tolerates missing pipelines, so a partial comparison can be generated now.

## Sources

`runs/kev/kev-0.8b-20261112-a`, `runs/kev/kev-4b-20261113-a`, `runs/kev/kev-9b-20261113-a`, `runs/laya/laya-multilingual-a` (`run.json`, `metrics_*.json`, `report_*.md`); `plans/HANDOFF.md`; `AGENT_BRIEF.md`.
