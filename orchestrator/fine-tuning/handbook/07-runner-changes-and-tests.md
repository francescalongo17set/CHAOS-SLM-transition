# 07 · Runner changes and tests

## Changes to the round-1 runners (small, on the pipeline branches)

- **`laya/run_laya.py`:** add `--checkpoint <dir>`. When given, `laya.load(<dir>, device=...)` replaces `laya.load(MODEL_REPO, subfolder=...)`. Keep the guard that the loaded config is multilingual (compare `max_len`, `head_max_len` and encoder name with the base config). Log `finetuned_from` (base repo and revision), `weights_sha256`, `train_run_id` and the applied temperatures. The resume rule (same revision) stays.
- **`kev/run.py`:** `--model <local checkpoint dir>` is already accepted by `Checkpoint`. Add logging of `finetuned_from` (size and pinned revision), adapter and `head.pt` sha256, `train_run_id`, and the fitted temperature (the shipped temperature is already logged from the loaded meta). Evaluate on the same dtype and path as the size's zero-shot run: 0.8B fp32 like `kev-0.8b-20261112-a`; 4B bf16 on one T4 like `kev-4b-20261113-a`.
- **Raw and calibrated ECE (FT-C-15):** each runner must make it possible to compute both. For Kev, `KEV_TEMPERATURE=1.0` gives raw probabilities; for Laya set the temperatures to 1 or store logits. If the existing log schema cannot hold both, stop and ask before changing it (the schema is baselines chapter 06).
- **Both:** the bundle builder (`kev/make_bundle.py` pattern) ships the `fine-tuning/` code and the checkpoint as a private Kaggle Dataset.
- **Also fix while there (known round-1 logging issues):** `run.py` should record the adapter **and** base disk size and `weights_sha256` (they were corrected by hand for 0.8B); `disk_mb_base` was null for 4B and 9B. Do this only on the new branches and say so in the plan.

Latency from fine-tuned runs is comparable with zero-shot only on the same hardware and dtype (chapter 03).

## Tests to write (`common/tests`, no GPU needed)

1. **Question parity:** for every train row, the built question objects equal what the eval adapter sends (text, options, order).
2. **Dispatcher on training labels:** labels of the built examples, mapped through the dispatcher, reproduce `support.expected_route` on 100% of train rows (gold record from labels plus slot status). This is the round-1 oracle test applied to the training files.
3. **Rule table of chapter 02:** no complexity question on out-of-scope or quick_reply rows; no slot question without gold; `insurer` skipped on the 100 train rows; `date_reference` never asked.
4. **Split assertions** of chapter 02 on the real data and on a synthetic leaky split (which must fail).
5. **Label validity:** every Kev label is a key of its `criteria`; every Laya `expected` value is in its `criteria`.
6. **State format:** `state` in both formats is a string equal to the `serialize_state` output.
7. **Bootstrap:** the paired bootstrap on a synthetic log with a known difference (interval excludes zero as expected) and on identical logs (interval contains zero).

A test that fails is not edited to pass. It stops the step and goes to the owner.
