# Orchestrator fine-tuning, round 2: Kev-0.8B run report and comparison

Snapshot 14 Nov 2026. Companion to `orchestrator/baselines/runs/RUNS_REPORT_v2.md` (zero-shot, v2 protocol), which stays as written. This report covers the first fine-tuning run, **Kev-0.8B** (`kev-0.8b-ft-a`), and compares it with its own zero-shot v2 run (`kev-0.8b-v2-20261113-a`). Laya and Kev-4B are not started.

Numbers come from `runs/kev/kev-0.8b-ft-a/` (`metrics_{test,validation}.json`, `report_*.md`, `run.json`, `train_report.json`, `calibration/temperature.json`) and from the zero-shot run folder above. Same hardware (Kaggle T4), same splits (test 593 rows, validation 298), same v2 question set (`questions.en.yaml`, state template p-01), 0 error rows, 0 truncated, dispatcher oracle 593/593 and 298/298 on the fine-tuned run.

**Do not rank on small gaps.** One training run (seed 0), one evaluation per split, no variance estimate. The size of the gain below is large enough that the direction is not in doubt; the third decimal is.

## 0. What was trained (read this first)

| | |
|---|---|
| Start point | released `jaredpalmer/kev-0.8b` at `9a45d25e` (LoRA 16, pointer head), warm start (372 LoRA tensors + head) |
| Data | `final_v2` train split: 1,903 records, 3 questions at most per record (scope, feature, complexity), no slot questions (FT-C-26). Calibration 189 records, development (= validation) 298, test 593 |
| Recipe | lr 2e-5, 1 epoch, batch 1 x accum 8 (released: batch 4 x accum 2, same effective batch 8), fp32 (released: bf16 autocast), checkpointing 1, seed 0, LoRA on all targets |
| Calibration | temperature fitted on the 189 calibration records (514 questions, min NLL): **T = 1.3195** (released value 2.351, previous 1.0) |
| Weights | `adapter_sha256` `bc80ff99...c52b`, `head_sha256` `0f054e2e...20e6`. Private Kaggle Dataset, not in git |
| Test split | run **once**, after validation was reviewed and `FROZEN = True` was set by hand (FT-C-14, FT-C-27) |

The earlier smoke and pilot folders (`kev-0.8b-ft-a-c1`, `-c2`, `eval-smoke`) are checks, not results. The c1 folder from before v2 was stale and was overwritten.

## 1. How the run went

| | Kev-0.8B fine-tuned | Kev-0.8B zero-shot v2 |
|---|---|---|
| Run id | `kev-0.8b-ft-a` | `kev-0.8b-v2-20261113-a` |
| dtype / hardware | float32, 1 x T4 | float32, 1 x T4 |
| Parameters | 0.75B | 0.75B |
| Disk (MB) | 1835 (adapter 65.5 + base 1769.9) | 1835 |
| Peak GPU, inference | 3.46 GB | 3.22 GB |
| Load time | 25.3 s | 7.6 s |
| Temperature applied | 1.3195 (fitted on v2) | 2.351 (released, fitted on v1) |

Training:

| | |
|---|---|
| Optimizer steps / records seen | 238 / 2,877 (about 3 questions per request), 0 rejected, 0 truncated |
| Wall time | 3,368 s (56 min); mean step 13.1 s after the first two |
| Peak GPU, training | 3.78 GB (T4 has 15.6 GB) |
| Loss | 1.03 (step 10), 0.61 (50), 0.36 (90), about 0.35 to 0.50 from step 130 to 238 |
| Gradient norm | mean 13.4, max 49.3, **238 of 238 steps clipped** |
| Pilot projection | c2 projected about 1.2 h of the 2 h box; real training plus calibration fit inside it |

Notes:
- Every optimizer step was gradient-clipped, so the clip is always active. It did not prevent learning at lr 2e-5, but it matters before raising lr toward the 5e-5 cap.
- Inference load time is longer (25.3 s vs 7.6 s), probably a cold start on a new session; not investigated.
- It is **not verified** whether the `causal_conv1d` wheel (FT-C-25) was active in this run: the logs do not mention it either way. Treat latency as unverified in that respect.

## 2. Fine-tuned vs zero-shot (test split, 593 rows)

| Metric | Kev-0.8B fine-tuned | Kev-0.8B zero-shot v2 |
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
| parameters / peak GPU | 0.75B / 3.5 GB | 0.75B / 3.2 GB |

Bold marks the better value in the row. Output tokens were not recorded.

### Per-route precision / recall (test)

| Route (support) | Fine-tuned | Zero-shot v2 |
|---|---|---|
| lightweight (201) | 0.81 / 0.94 | 0.64 / 0.70 |
| agentic (243) | 0.94 / 0.91 | 0.74 / 0.80 |
| refuse (95) | 0.87 / 0.63 | 0.92 / 0.13 |
| quick_reply (54) | 0.98 / 0.96 | 0.42 / 0.76 |

### Refuse recall by leak type (test)

| Type (gold rows) | Fine-tuned | Zero-shot v2 |
|---|---|---|
| prompt_injection (18) | 0.56 | 0.00 |
| data_extraction (5) | 0.60 | 0.00 |
| fraud_or_illegal (5) | 0.40 | 0.00 |
| jailbreak (4) | 0.75 | 0.50 |
| social_engineering_or_abuse (3) | 1.00 | 0.00 |

### Where wrong routes first go wrong (test)

| First wrong field | Fine-tuned | Zero-shot v2 |
|---|---|---|
| scope_check | 46 | 126 |
| feature_classification | 9 | 49 |
| complexity_estimation | 15 | 30 |
| **total wrong routes** | 70 | 205 |

### Validation split (298 rows)

| Metric | Fine-tuned | Zero-shot v2 |
|---|---|---|
| scope accuracy | 0.930 | 0.799 |
| feature accuracy | 0.876 | 0.664 |
| complexity accuracy | 0.888 | 0.772 |
| route accuracy | 0.889 | 0.678 |
| route macro-F1 | 0.889 | 0.596 |
| refuse recall | 0.792 | 0.208 |
| mean latency (ms) | 279 | 277 |

The sanity check (FT-C-12: validation route macro-F1 above the zero-shot 0.596) passed, 0.889.

### What this shows

1. **Fine-tuning lifts every question and the route by a large margin.** Test route accuracy goes from 0.654 to 0.882 and macro-F1 from 0.550 to 0.874; wrong routes fall from 205 to 70. Validation and test agree (0.889 vs 0.874 macro-F1), so there is no sign of tuning to the development split.
2. **Most of the gain is at the scope gate.** First-wrong-field errors at `scope_check` drop from 126 to 46, mainly because refuse recall rises from 0.126 to 0.632. Refuse precision falls slightly (0.92 to 0.87), a fair trade.
3. **Refusal is still the weakest part.** 35 of 95 test refuse rows are missed; fraud_or_illegal (0.40) and prompt_injection (0.56) are lowest. Recall on test (0.632) is clearly lower than on validation (0.792), and these groups are small (5 and 18 test rows), so read them as indicative only.
4. **Calibration improved a lot.** ECE is 0.02 to 0.03 on all three questions, against 0.11 to 0.27 zero-shot. Part of that is the new temperature (1.32 fitted on v2 vs the v1-era 2.35); this report does not separate the effect of tuning from the effect of re-fitting T.
5. **Cost is unchanged**: same model size, same input tokens (381), mean latency 248 vs 286 ms, within what the dtype and kernel caveat allows.

## 3. Caveats that must travel with these numbers

- **One run, one seed.** No variance estimate and no paired bootstrap yet (FT-P-04, chapter 03 test 7, still to build). The report states differences, not significance.
- **Zero-shot is the own-model reference** (round 2, v2 protocol). Laya has no fine-tuned run, so no cross-model fine-tuned comparison exists yet.
- **Recipe differs from the released one** in batch/accum split and fp32 vs bf16 autocast; the effective batch is the same (8).
- **Temperature and training are confounded** in the calibration result (point 4 above). Raw ECE (FT-C-15, `softmax(T * log p)`) is not computed.
- **Latency** is not verified against the `causal_conv1d` state (section 1) and the zero-shot run used the fallback path, so the 248 vs 286 ms gap should not be quoted as a speed-up.
- **Test used once.** The configuration is frozen (FT-C-27); any rerun must be identical, not a new configuration.
- **Refusal numbers are noisy** (small groups; validation and test differ by 16 points on recall).
- **Version control:** weights are not in git. Only logs, metrics, reports and `run.json` are committed.

## 4. Next steps

1. Paired bootstrap and the comparison table (`common/compare.py` style), reporting intervals and no decision rule (FT-C-14).
2. Raw vs calibrated ECE (FT-C-15) to separate the temperature effect from the training effect.
3. Record the private Kaggle Dataset name and the session length and weekly quota in HANDOFF (chapter 09 item 6).
4. Kev-4B (FT-P3, bf16, 3 h box) and Laya (FT-P1, code not written).
