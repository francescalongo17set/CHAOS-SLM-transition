# Orchestrator fine-tuning, round 2: Kev-0.8B and Laya run report and comparison

Snapshot 14 Nov 2026. Companion to `orchestrator/baselines/runs/RUNS_REPORT_v2.md` (zero-shot, v2 protocol), which stays as written. This report covers the two fine-tuning runs that exist, **Kev-0.8B** (`kev-0.8b-ft-a`) and **Laya multilingual** (`laya-ft-multilingual-a`), each compared with its own zero-shot v2 run (`kev-0.8b-v2-20261113-a`, `laya-v2-a`), and then with each other. Kev-4B is not started.

Numbers come from `runs/kev/kev-0.8b-ft-a/` and `runs/laya/laya-ft-multilingual-a/` (`metrics_{test,validation}.json`, `report_*.md`, `run.json`, `train_report.json`, plus `calibration/temperature.json` for Kev and `epochs.jsonl` for Laya) and from the zero-shot run folders above. Same hardware (Kaggle T4), same splits (test 593 rows, validation 298), same v2 question set (`questions.en.yaml`, state template p-01), 0 error rows, 0 truncated, and the dispatcher oracle matches 593/593 (test) and 298/298 (validation) on every run in this report.

**Do not rank on small gaps.** One training run each (seed 0), one evaluation per split, no variance estimate. The gains over zero-shot are large enough that the direction is not in doubt; the third decimal, and the gap between the two fine-tuned models, are not.

## 0. What was trained (read this first)

| | Kev-0.8B | Laya multilingual |
|---|---|---|
| Start point | released `jaredpalmer/kev-0.8b` at `9a45d25e` (LoRA 16 + pointer head), warm start | `convaiinnovations/laya/multilingual` at `85cc74dd` (encoder + decision head) |
| Data | `final_v2` train, 1,903 records, 3 questions at most per record, no slot questions (FT-C-26) | same split, 5,239 training items, calibration 514, development 894 |
| Recipe | lr 2e-5, 1 epoch, batch 1 x accum 8, fp32, checkpointing 1, LoRA on all targets, seed 0 | 4 epochs, micro-batch 8 x accum 8, encoder lr 2.5e-5, head lr 1e-4, loss `rlcd`, AMP, seed 0 |
| Selection | none (1 epoch) | epoch with the best development route macro-F1: **epoch 4** of 4 |
| Calibration | T = **1.3195** (189 records, 514 questions, min NLL) | T = **[5.0, 1.0, 1.0]**: the fitted value 5.62 hit the **upper clamp** 5.0 |
| Weights | adapter `bc80ff99...c52b`, head `0f054e2e...20e6` | `d0f3f358...1f41` (sha256 of the checkpoint) |
| Test split | run **once**, after validation was reviewed and `FROZEN = True` (FT-C-14, FT-C-27) | run **once**, same rule |

Weights of both runs are in private Kaggle Datasets, not in git. The earlier smoke and pilot folders (`kev-0.8b-ft-a-c1`, `-c2`, `laya-ft-multilingual-a-b1`, `eval-smoke/`) are checks, not results.

## 1. How the runs went

| | Kev-0.8B fine-tuned | Laya fine-tuned |
|---|---|---|
| Run id | `kev-0.8b-ft-a` | `laya-ft-multilingual-a` |
| Training wall time | 3,368 s (238 steps, 2,877 records seen) | 896 s (4 epochs of about 196 to 202 s), 957 s total |
| Peak GPU, training | 3.78 GB | 6.19 GB |
| Loss | 1.03 (step 10) to about 0.35 (last 100 steps) | epoch mean 0.476, 0.453, 0.285, 0.153 |
| Gradient clipping | every step clipped (norm mean 13.4, max 49.3) | not recorded in this report |
| Inference dtype / hardware | float32, 1 x T4 | fp16, 1 x T4 |
| Parameters | 0.75B | 0.32B |
| Disk (MB) | 1835 | 678 |
| Peak GPU, inference | 3.46 GB | 1.53 GB |
| Load time | 25.3 s (zero-shot 7.6 s) | 16.6 s (zero-shot 8.1 s) |
| Sanity check (FT-C-12) | validation route macro-F1 0.889 > 0.596 | best development route macro-F1 0.918 > 0.395 |

Laya development route macro-F1 per epoch (validation, 298 rows): 0.395 (start) → 0.854 → 0.908 → 0.917 → **0.918**. Most of the gain is in the first two epochs; epochs 3 and 4 add 0.01 each, while the training loss keeps falling (0.285 to 0.153).

Notes:
- Kev: every optimizer step was gradient-clipped. It did not stop learning at lr 2e-5, but it matters before raising lr toward the 5e-5 cap. The pilot projected about 1.2 h of the 2 h box; the real run fit.
- Kev: it is **not verified** whether the `causal_conv1d` wheel (FT-C-25) was active; the logs do not say. Latency is therefore unverified in that respect.
- Laya: the epoch was chosen on the development split, which is also the validation split of this report. Test was not used for selection.
- Laya: training peak memory (6.2 GB) is much larger than inference (1.5 GB) because of the encoder backward pass.

## 2. Kev-0.8B: fine-tuned vs zero-shot (test split, 593 rows)

| Metric | Fine-tuned | Zero-shot v2 |
|---|---|---|
| scope_check accuracy / macro-F1 | **0.922** / **0.885** | 0.788 / 0.553 |
| feature accuracy / macro-F1 | **0.874** / **0.878** | 0.663 / 0.693 |
| complexity accuracy / macro-F1 | **0.883** / **0.882** | 0.727 / 0.726 |
| **route accuracy** (4 routes) | **0.882** | 0.654 |
| **route macro-F1** | **0.874** | 0.550 |
| refuse recall (all 95) | **0.632** | 0.126 |
| refuse precision | 0.87 | **0.92** |
| ECE scope / feature / complexity | **0.030** / **0.021** / **0.018** | 0.271 / 0.181 / 0.107 |
| mean latency (ms) | 248 | 286 |
| native input tokens (mean) | 381 | 381 |

Per-route precision / recall (test):

| Route (support) | Fine-tuned | Zero-shot v2 |
|---|---|---|
| lightweight (201) | 0.81 / 0.94 | 0.64 / 0.70 |
| agentic (243) | 0.94 / 0.91 | 0.74 / 0.80 |
| refuse (95) | 0.87 / 0.63 | 0.92 / 0.13 |
| quick_reply (54) | 0.98 / 0.96 | 0.42 / 0.76 |

First wrong field (test): scope_check 46 (zero-shot 126), feature 9 (49), complexity 15 (30); **70 wrong routes against 205**.

Validation (298 rows): route accuracy 0.889 (zero-shot 0.678), macro-F1 0.889 (0.596), scope 0.930 (0.799), feature 0.876 (0.664), complexity 0.888 (0.772), refuse recall 0.792 (0.208).

What this shows:
1. Fine-tuning lifts every question and the route. Validation and test agree (0.889 vs 0.874 macro-F1).
2. Most of the gain is at the scope gate, mainly because refuse recall rises from 0.126 to 0.632 while precision falls only from 0.92 to 0.87.
3. Refusal is still the weakest part (35 of 95 test refuse rows missed; fraud_or_illegal 0.40, prompt_injection 0.56, small groups). Test recall (0.632) is well below validation (0.792).
4. Calibration is much better (ECE 0.02 to 0.03 against 0.11 to 0.27), but this mixes the training effect with the re-fitted temperature (1.32 vs the v1-era 2.35).

## 3. Laya: fine-tuned vs zero-shot (test split, 593 rows)

| Metric | Fine-tuned | Zero-shot v2 |
|---|---|---|
| scope_check accuracy / macro-F1 | **0.960** / **0.936** | 0.649 / 0.546 |
| feature accuracy / macro-F1 | **0.889** / **0.891** | 0.337 / 0.349 |
| complexity accuracy / macro-F1 | **0.881** / **0.880** | 0.523 / 0.378 |
| complexity recall, `complex` / `simple` | **0.87** / 0.89 | 0.04 / **0.97** |
| **route accuracy** (4 routes) | **0.916** | 0.415 |
| **route macro-F1** | **0.916** | 0.421 |
| refuse recall (all 95) | **0.853** | 0.411 |
| refuse precision | **0.90** | 0.25 |
| ECE scope / feature / complexity | **0.019** / **0.031** / **0.084** | 0.117 / 0.409 / 0.326 |
| mean latency (ms) | 32.5 | 32.5 |
| native input tokens (mean) | 551 | 551 |
| parameters / peak GPU | 0.32B / 1.5 GB | 0.32B / 1.5 GB |

Per-route precision / recall (test):

| Route (support) | Fine-tuned | Zero-shot v2 |
|---|---|---|
| lightweight (201) | 0.86 / 0.95 | 0.45 / 0.59 |
| agentic (243) | 0.97 / 0.91 | 0.53 / 0.21 |
| refuse (95) | 0.90 / 0.85 | 0.25 / 0.41 |
| quick_reply (54) | 0.96 / 0.94 | 0.47 / 0.69 |

Refuse recall by leak type (test): prompt_injection (18) 1.00 (zero-shot 0.39), data_extraction (5) 0.80 (0.80), fraud_or_illegal (5) 0.80 (0.60), jailbreak (4) 1.00 (1.00), social_engineering_or_abuse (3) 0.67 (0.67).

First wrong field (test): scope_check 24 (zero-shot 208), feature 8 (120), complexity 18 (19); **50 wrong routes against 347**.

Validation (298 rows): route accuracy 0.930 (zero-shot 0.393), macro-F1 0.918 (0.395), scope 0.946 (0.614), feature 0.933 (0.406), complexity 0.915 (0.522), refuse recall 0.875 (0.292).

What this shows:
1. **The largest gain of the round.** Route accuracy goes from 0.415 to 0.916 at no cost in size or speed (same 0.32B, same 32.5 ms, same 1.5 GB).
2. **The zero-shot failure modes are gone.** Zero-shot Laya predicted `simple` for 96.5% of in-scope rows (`complex` recall 0.04) and had feature accuracy 0.337; fine-tuned, `complex` recall is 0.87 and feature accuracy 0.889. Refuse precision rises from 0.25 to 0.90, so the model now refuses on purpose, not at random.
3. **Complexity is the weakest calibrated question** (ECE 0.084), against 0.019 and 0.031 for scope and feature.
4. **Test is a little lower than validation** on every question (route macro-F1 0.916 vs 0.918, feature 0.889 vs 0.933); small, and expected because epoch selection used the validation split.

## 4. The two fine-tuned models side by side (test split)

| Metric | Kev-0.8B fine-tuned | Laya fine-tuned |
|---|---|---|
| scope accuracy / macro-F1 | 0.922 / 0.885 | **0.960** / **0.936** |
| feature accuracy / macro-F1 | 0.874 / 0.878 | **0.889** / **0.891** |
| complexity accuracy / macro-F1 | **0.883** / **0.882** | 0.881 / 0.880 |
| **route accuracy** | 0.882 | **0.916** |
| **route macro-F1** | 0.874 | **0.916** |
| refuse recall / precision | 0.632 / 0.87 | **0.853** / **0.90** |
| refuse recall, prompt injection (18) | 0.56 | **1.00** |
| wrong routes (of 593) | 70 | **50** |
| ECE scope / feature / complexity | 0.030 / **0.021** / **0.018** | **0.019** / 0.031 / 0.084 |
| mean latency (ms) | 248 | **32.5** |
| parameters / peak GPU (inference) | 0.75B / 3.5 GB | **0.32B / 1.5 GB** |
| training wall time | 3,368 s | **896 s** |

Bold marks the better value in the row. Validation tells the same story (route macro-F1 0.918 Laya, 0.889 Kev).

Findings:
1. **After fine-tuning the order of round 1 flips.** Zero-shot, Kev-0.8B was far ahead (route accuracy 0.654 vs 0.415). Fine-tuned, Laya is ahead on route accuracy (0.916 vs 0.882), on refusal, and on cost, with Kev ahead only on calibration of feature and complexity. The gap is small (34 routes of 593) and has no interval yet.
2. **Laya improves much more because it started much lower**, not because the end point is far apart: the two models finish within 0.04 of each other on route accuracy.
3. **Refusal separates them most** (0.853 vs 0.632 recall, prompt injection 1.00 vs 0.56), which is where Kev-0.8B was already weakest zero-shot.
4. **Cost favours Laya clearly**: less than half the parameters, under half the GPU memory, about 7.6 times lower mean latency, and 3.8 times shorter training. The latency comparison keeps the round-1 caveats (fp16 vs fp32, Kev on an unverified kernel path).

## 5. Caveats that must travel with these numbers

- **One run each, one seed.** No variance estimate and no paired bootstrap yet (FT-P-04, chapter 03 test 7, still to build). Differences are stated, not tested; the Kev-vs-Laya gap especially.
- **Different recipes.** Kev: 1 epoch, LoRA, no model selection. Laya: 4 epochs, full encoder, best of 4 epochs chosen on the development split, different data granularity (items vs records). The comparison is between two tuned systems, not between two models under one recipe.
- **Laya's temperature hit the clamp** (fitted 5.62, applied 5.0), a calibration issue flagged by the trainer; the choice temperature is therefore not the fitted optimum. ECE is still low (0.02 to 0.08).
- **Temperature and training are confounded** in both calibration results. Raw ECE (FT-C-15, `softmax(T * log p)`) is not computed.
- **Laya's epoch 4 is at the edge of the search**: more epochs were not tried, and the validation gain was already small (0.917 to 0.918).
- **Latency** is not comparable across dtypes and, for Kev, not verified against the `causal_conv1d` state; do not quote Kev's 248 vs 286 ms as a speed-up.
- **Test used once per model.** Both configurations are frozen (FT-C-27 for Kev); a rerun must be identical, not a new configuration.
- **Refusal numbers are noisy** (small leak-type groups of 3 to 18 rows; Kev validation and test recall differ by 16 points).
- **Version control:** weights are not in git. Only logs, metrics, reports and `run.json` are committed.

## 6. Next steps

1. Paired bootstrap and the comparison table (`common/compare.py` style), reporting intervals and no decision rule (FT-C-14); Kev-vs-Laya included.
2. Raw vs calibrated ECE (FT-C-15), to separate temperature from training; revisit the Laya clamp.
3. Record the private Kaggle Dataset names and the session length and weekly quota in HANDOFF (chapter 09 item 6).
4. Kev-4B (FT-P3, bf16, 3 h box). Open: resolve the short pin `139fdd94`.
