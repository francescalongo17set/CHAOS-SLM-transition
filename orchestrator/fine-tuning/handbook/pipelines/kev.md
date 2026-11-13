# 06 · Pipeline: Kev (0.8B and 4B)

Branches: `orchestrator/ft-kev-0.8b` (priority 2) and `orchestrator/ft-kev-4b` (priority 3), FT-C-03. Read first: chapters 01 to 04. Facts marked *(upstream)* come from the Kev source read on 13 Nov 2026 (`kev` `main`: `train.py`, `data.py`, calibration scripts); nothing here has been run. Everything applies to both sizes unless the table below says otherwise.

## Per-size parameters

| | Kev-0.8B | Kev-4B |
|---|---|---|
| Run id | `kev-0.8b-ft-a` | `kev-4b-ft-a` |
| `--init_from` | `jaredpalmer/kev-0.8b` at a **pinned commit** (round 1 loaded Hub tag `v1.0` as commit `bf75a6a8`; the card's weights revision is `9a45d25e`, adapter and head hashes identical). Pin the commit; tags move. | `jaredpalmer/kev-4b@139fdd94` (baselines C-32) |
| Base | Qwen3.5-0.8B-Base (revision from the checkpoint meta) | Qwen3.5-4B-Base (revision from the checkpoint meta) |
| Training dtype | `--dtype fp32 --weights_dtype fp32` (the exact path the model was built for) | `--dtype bf16 --weights_dtype bf16` (fp32 does not fit one T4, baselines C-32) |
| `--checkpointing` | 0 first; 1 only if the pilot runs out of memory | 1 |
| Released temperature (stale after fine-tuning) | 2.351 | 2.406 |
| Round-1 inference | 431 ms per row (two calls), 3.2 GB peak GPU | 3.64 s per row, 8.9 GB peak GPU |
| Training time per epoch on about 1,880 records (estimate, to be measured) | about 30 to 60 min | about 3 h |
| Hardware | one Kaggle T4, free | one Kaggle T4, free (FT-C-08: no paid exception) |
| Time box (FT-C-13) | 2 h | 3 h |
| Sanity check (FT-C-12) | development route macro-F1 above **0.357** | development route macro-F1 above **0.483** |

Kev-0.8B is compared with its own zero-shot run; comparing it with zero-shot 4B or 9B is context, not a like-for-like gain.

## Environment

See chapter 04: upstream `kev` pinned at the round-1 commit `2074cc4`, `flash-linear-attention==0.5.2`, Python 3.12+, Kaggle T4, `causal_conv1d` not installed (latency labelled "fallback").

## What trains *(upstream)*

`python -m kev.train` trains a **LoRA adapter plus a pointer head** on the frozen backbone. LoRA: rank `--lora` (16), alpha 2r, dropout 0.05, PEFT. Targets `--lora_targets` (`all` = q,k,v,o,gate,up,down plus the Gated-DeltaNet projections on hybrid backbones). Head: `--head_dim` 256. Per question, cross-entropy on the pointer-head distribution; AdamW with two groups (LoRA at `--lr`, head at `--head_lr`, 0 means the same), OneCycle schedule with `pct_start` 0.1, gradient clip 1.0, loss divided by records per step, a non-finite loss raises. One optimizer step sees `accum × batch` records (defaults accum 8, batch 1).

## Warm start and the architecture check

Use `--init_from jaredpalmer/kev-<size>@<pinned revision>`. `warm_start` raises on any mismatch of `base`, `base_revision`, `lora`, `head_dim`, `option_isolation`, `special_embeddings`, `weights`. So **read the released checkpoint's meta first** (`kev.checkpoint.read_meta`) and pass the same values explicitly: `--base`, `--base_revision`, `--lora`, `--head_dim`, `--lora_targets`, `--option_isolation`, `--special_embeddings`, `--weights_dtype`. The official Modal script does exactly this and takes `lr`, `batch`, `accum`, `checkpointing` from `meta.extra["args"]`. Our wrapper `kev/train_kev.py` does the same, prints the meta, and writes it into our `run.json`. The default base of `kev.train` is `Qwen/Qwen3-0.6B-Base`: **never rely on defaults**.

## Command and hyperparameters (FT-C-10: keep as proposed)

```
python -m kev.train \
  --data data/kev/train.jsonl  --init_from jaredpalmer/kev-<size>@<rev> \
  --out runs/kev-<size>-ft-a/checkpoint \
  --device cuda --dtype <fp32|bf16> --weights_dtype <fp32|bf16> --checkpointing <0|1> \
  --lr 5e-5 --epochs 1 --batch 1 --accum 8 --p_none_pair 0.25 --seed 0 \
  <architecture args copied from the checkpoint meta>
```

| Parameter | Value | Why |
|---|---|---|
| `--lr` | `min(meta lr, 5e-5)` | The Modal script caps a delta at `MAX_DELTA_LR = 5e-5` (released deltas used 2e-5 to 4e-5). The `kev.train` default 2e-4 is for from-scratch training. |
| `--epochs` | 1, then at most 2 if development improves | Modal default is 1. With the 4B time box (3 h at about 3 h per epoch) a second epoch will not fit; the plan must say so. |
| `--dtype` + `--weights_dtype` | per-size table | `--dtype bf16` requires `--device cuda`; only `fp32` and `bf16` exist (no fp16). bf16 is emulated on a T4. |
| `--batch 1 --accum 8` | defaults | one record holds up to 7 isolated questions; 8 records per step. |
| `--p_none_pair 0.25` | as Modal | adds none-option minimal pairs; harmless to our questions. |
| `--replay` | 0 (FT-P-08) | needs the public `decision-v7` suite (`--suite`), not available offline; if it is available in session, record it and ask. |
| `--max_state` | default 384 | our states are at most 220 tokens. |
| Multi-GPU | not used | `torchrun`/FSDP2 is documented only for `--full_ft 1`; `--row_budget` is disallowed under `torchrun`. LoRA training is single GPU. |

**Augmentation (FT-C-10: shuffling is okay).** `kev.train` augments records (`augment`: option shuffling, none-option and distractor options) controlled by `--p_none`, `--p_none_distract`, `--p_distract` (defaults 0.1, 0.12, 0.15). Keep the defaults. The in-session check (chapter 09) establishes whether records from `--data` pass through `augment`; record the finding in `run.json` notes. Evaluation uses canonical option order; shuffling during training is expected to be harmless, and the run log must still state the augmentation settings.

**Class imbalance (FT-C-10).** Upstream does not handle it (`--label_smoothing`, `--brier_w`, `--focal_gamma` exist and default to 0). Do **not** use them in the first run. They are the levers for the `lightweight` and clarification problems if the first run shows them; using them needs the owner's go-ahead (a second configuration).

## Calibration

Fine-tuning shifts the logits, so the released temperature (2.351 for 0.8B, 2.406 for 4B) is stale. After training:

1. Score `calibration.jsonl` with `KEV_TEMPERATURE=1.0` (raw logits) using `kev.benchmark.evaluate_records` / `kev.predictors.LocalPredictor`.
2. Fit `kev.metrics.fit_temperature(rows, aggregation="micro")` (minimum NLL, the upstream method).
3. Write it with `scripts/calibrate_checkpoint.py --run <checkpoint> --temperature T --reason "fit on our calibration partition, n=..."`. The `--temperature` path skips the script's in-distribution refusal (it would refuse our rows as "training data"); that is why this manual path is used.

The temperature is stored in `head.pt` (`meta.temperature`, `extra.temperature_fit`); the argmax never changes. **Report ECE raw (T=1) and calibrated side by side** (FT-C-15): the evaluation runs once with `KEV_TEMPERATURE=1.0` and once with the fitted temperature, or stores logits; decide in the plan.

## Cost and risk *(estimates, to be measured)*

**0.8B.** Memory: fp32 weights about 3 GB plus LoRA, Adam states and activations at batch 1; expected well inside 16 GB (round-1 inference peak 3.2 GB). Time: round-1 inference was 0.43 s per row for two calls; one training record is about one call-equivalent and forward plus backward is about 3 to 4× a forward, so **expect about 30 to 60 min per epoch**. Residual risk: capacity (weakest Kev, English-only card, weak Italian zero-shot). A smaller gain than the 4B is a result, not a failure.

**4B.** Memory: bf16 backbone about 8.4 GB plus LoRA, optimizer states and checkpointed activations; expected to fit a 16 GB T4 at batch 1 (round-1 inference peak 8.9 GB). Time: round-1 inference took 3.6 s per row for two calls on this path; one training record is about one call-equivalent, and forward plus backward plus recompute is about 4× a forward, so **expect about 3 h per epoch** on about 1,880 records, **at the edge of the 3 h box**. The pilot (C2) measures it. If the projection exceeds the box, **stop and ask**. A paid run is not an option (FT-C-08); the owner may widen the box or choose another route. Re-check Kaggle's session and weekly GPU limits in session.

## Steps and checks (once per size, 0.8B first)

| # | Step | Check that can fail |
|---|---|---|
| C0 | Read `kev/train.py` and `kev/data.py` at the pinned sha; answer the Kev items of chapter 09. | Written in `run.json` notes. |
| C1 | Smoke: 32 records, `--max_steps 1`, reload with `kev/run.py --model <dir>`. | Loss finite; checkpoint loads; `base_revision` equals the pinned one (4B: `139fdd94`; 0.8B: the commit recorded in the table). |
| C2 | Pilot: 300 records, 1 epoch; log step time and peak memory; project the full run. | Projection inside the time box, else stop and ask. |
| C3 | Full run, then calibration. | Sanity check (FT-C-12): development route macro-F1 above the size's zero-shot (0.8B: 0.357; 4B: 0.483), else stop and report. |
| C4 | Evaluate (chapter 03): validation, then test once. | `validate_log` clean; 0 error rows; oracle 593/593. |

**Time box (FT-C-13):** C2 and C3 together (pilot, full run, calibration) must fit 2 h for 0.8B and 3 h for 4B. C4 is separate.

**Ordering (FT-P-02):** the 4B branch starts only after the 0.8B run has finished C0 and C1, because those steps answer, once for every Kev size, the upstream-trainer questions of chapter 09.

## Checkpoint handling

The trained adapter and `head.pt` (small: round-1 adapters were 65 MB for 0.8B, 160 MB for 4B) go to a private Kaggle Dataset (FT-P-06). Record `adapter_sha256` and `head_sha256`, `train_run_id`, the pinned `finetuned_from` revision, and the fitted temperature in `run.json`.

## Acceptance criteria

- `train_report.json` and `run.json` complete (meta of the released checkpoint, arguments, augmentation settings, temperatures, hashes).
- Validation and test logs validated, oracle 593/593, 0 error rows.
- Comparison with the size's zero-shot run, including bootstrap intervals (chapter 03).

## Stop-and-ask triggers

`kev.train` records not accepted · architecture mismatch on warm start · any record dropped by `kev.model.fits` · pilot projection beyond the time box · sanity check failed · NaN loss · any item of chapter 09 that fails.
