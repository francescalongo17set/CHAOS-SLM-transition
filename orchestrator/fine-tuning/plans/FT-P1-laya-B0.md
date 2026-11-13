# FT-P1 Laya · B0 notes (chapter 09 item 4, plan open item 2)

Read 14 Nov 2026 from the `laya==0.4.31` wheel, run locally on CPU (no weights, no training). Revision `convaiinnovations/laya` @ `85cc74ddae6109077ebe2853a9b3077fb6606a78`, subfolder `multilingual`.

## Chapter 09 item 4

| Check | Result |
|---|---|
| `read_data` accepts our JSONL with `expected` | **Yes.** `.jsonl` goes to `read_jsonl`. With the real multilingual tokenizer, `items_from_rows(tok, rows, 1024, 256)` gave train 1,903 rows → 5,239 items, calibration 189 → 514, development 298 → 820; **`skipped` = `{}` on all three**. |
| Question ids with `:` | **Not applicable in v2.** Ids are `scope_check`, `feature_classification`, `complexity_estimation` (the last on 1,433 / 136 / 224 rows only); no id contains `:`. |
| `laya.load(<local dir>)` on a saved checkpoint | **Not run** (needs weights). Source: `save_checkpoint` writes fp16 `model.safetensors`, `encoder/` config, `tokenizer/`, `rl_agent_config.json`, the layout `load` reads. Check in B1. |
| `train_model` signature | `(model, tok, items, config, device, max_len, head_max_len, on_epoch_end=None, parallel=False) -> List[float]` |
| `on_epoch_end` | `Callable[[int, float], None]`, called `(epoch, mean_loss)`. No model argument: use a closure. |
| `collate_items` | `(batch, pad_id)`; `batch` is a list of groups of encoded items. |
| Multilingual `max_len` / `head_max_len` | **1024 / 256**, as expected. Longest state in our data: 229 tokens. |
| Config extras | `temperature [1,1,1]`, `temperature_by_options {}`, no `binning_map`, `amp_dtype "bf16"` (T4 has no bf16: training uses fp16 autocast; check inference in B1). |

## Plan open item 2 (raw vs calibrated ECE)

- `Agent._decode_answers`: `z = raw_logits / t_scale`, softmax. `t_scale = temperature_by_options[temp_bucket(qtype, k)]` if present, else `temperature[qtype]`. So raw = `softmax(T * log p_cal)`, **as the plan assumed**.
- `temperature_by_options` needs `MIN_BUCKET_N = 2000` records per bucket. Calibration has **514** records, so the map stays empty and only the per-type scalar applies. `train_laya.py` must also drop the base `temperature_by_options` as `finetune` does.
- Fitted temperatures are clamped to `[0.5, 5.0]`; `fit_temperature_map` returns `temperature_clamped` (store it).
- `binning_map` only changes `answer_confidence`, not `probabilities`; none is fitted by our flow.
- **Precision:** `predict` rounds `probabilities` to 4 decimals. Raw recomputed from them is inexact for options with p < ~0.001, worse at large T. Top-1 confidence is barely affected. B4 check: recompute raw on a validation sample and compare top-1 against a real raw pass before relying on it. Fallback in the plan stays.

## Findings that change `train_laya.py`

1. `train_model` calls `model.train()` once before the epochs; `calibration_records` calls `model.eval()` and never restores it. Development scoring inside `on_epoch_end` must call `model.train()` afterwards, or epochs 2 to 4 train with dropout off. Needs a test.
2. `train_model` ends with `model.eval()`.
3. `finetune` has no per-epoch development scoring and does its own calibration split, so `train_laya.py` composes the lower-level functions (as the plan already says). Calibration comes from `calibration.jsonl`, not `split_calibration`.
4. `calibration_records` runs in fp32 (`amp=False`); development scoring per epoch will be slower than a fp16 pass. Measure in B2.
5. `TrainConfig` defaults equal the plan's config (4 epochs, 8 × 8, 2.5e-5, 1e-4, 1e-6, rlcd, `shuffle_options=()`, `label_smoothing` 0, seed 0).

## Still open

- `laya.load(<dir>)` reload and bf16/fp16 inference on the T4: B1.
- Chapter 09 items 5 (Laya CLI list is irrelevant, we call the library), 6 (Kaggle quota, check in session), 7 (answered above, confirm in B4).
