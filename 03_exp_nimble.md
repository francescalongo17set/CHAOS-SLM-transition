# 03. Experiment: Nimble (method adoption first, trainer second)

Status: DRAFT v0.1. Read `00_overview_and_rationale.md` and `01_data_spec_and_generation.md` first.

## 1. Goal and structure

Nimble gives us two different things:

- **Track A (default): adopt the method.** Contrastive data curation, dataset integrity checks and evaluation hygiene. This needs no large GPU.
- **Track B (conditional): run Nimble's trainer.** Its documented recipe trains a 9B model, which is probably too large for our hardware. Track B only proceeds if the go/no-go checks in section 6 pass.

## 2. What Nimble is (documented facts only)

- A recipe, data and a model for typed decisions: the model scores the allowed answer tokens directly and does not generate text. `[DOC: N-README, N-HF]`
- Input: a text (context) and a **flat** schema; each field is an enum (1 to 255 choices) or a boolean; ordered rating scales are scored from the probabilities. No nested fields, no free text out, text input only. `[DOC: N-README]`
- Training: LoRA (rank 16) on Qwen3.5-9B, cross-entropy over the allowed candidate logits only, one epoch, learning rate 5e-5, effective batch 8, seed 17, 2,048-token prompt limit, BF16. Tuning ran on L40S, the final fit on H100. `[DOC: N-README, N-TRAIN]`
- Training does not use generated reasoning or teacher probabilities, and Jev outputs were not used for training. `[DOC: N-README, N-TRAIN]`
- Data: synthetic, model-checked, not human-reviewed; 2,676 contrastive training records in the original release (2,826 in the later retained set, 2,676 contrastive plus 150 blind-reviewed complex cases) and a frozen 324-example holdout; 64 training source families disjoint from the holdout's families. `[DOC: N-README, N-DATASET]`
- Result: 90.1% agreement with reference labels on the 324 holdout examples, against 66.4% for the untuned 9B base and 93.2% for Jev. The holdout is narrow (162 pairs from six source families). `[DOC: N-README]`
- Probabilities: the latest published checkpoint uses temperature 1.0 without a separate fit; the original release used a fitted temperature of 2.179; thresholds from earlier releases must be re-tested. `[DOC: N-README, Updates]`
- Limits: prompts up to 8,192 tokens (trained on up to 2,048); fields cannot depend on each other. `[DOC: N-README]`
- Latency reported: 9B, median 106 ms on an H100 and 444 ms on an Apple M5 Pro 64 GB. `[DOC: N-README]`
- The CUDA scorer scores each field separately with the full prompt; the MLX scorer processes the shared context once. `[DOC: N-README]`
- **License: unverified.** The README we read does not state one; third-party pages disagree. Check the repo's `LICENSE` file and record the result before copying any code. `[NOT DOCUMENTED]`

## 3. Required reading

- `docs/TRAINING_EVAL_CURATION.md` (generation and replay guide): `[NOT READ by authors]`
- `docs/PARALLEL_SCORING.md` (schema rules): `[NOT READ by authors]`
- `docs/PUBLIC_BENCHMARKS.md`: `[NOT READ by authors]`
- `docs/NIMBLE_TRAINING.md` and `docs/DATASET.md` (read; use the commit-pinned versions linked in `00` section 7).
- The code in `nimble/datasets/` and `nimble/training/` before relying on any behaviour below.

## 4. Track A: adopt the method

### A1. Clone, pin, license

A1.1 `git clone https://github.com/bespokelabsai/nimble.git nimble` and record the commit hash. `[DOC: N-README]`

A1.2 Open the repo's `LICENSE` file (if any) and record its content in `RESULTS_NOTES.md`. If there is none, record that and do not copy code into our repository; implement the method from the documentation instead. `[OUR REQUIREMENT]`

### A2. Study the curation pipeline

A2.1 Read `docs/TRAINING_EVAL_CURATION.md`. Write `NIMBLE_FORMAT_NOTES.md` with: the record fields of the curated data, how evidence sentences and the "focus fact" are represented, how checks and their results are stored, how requests and responses are replayed offline. `[NOT DOCUMENTED]` until you read it.

A2.2 Locate the dataset files. The commit-pinned `DATASET.md` says `data/` stays local and git-ignored and that a fresh checkout needs `data/train.jsonl`, `data/eval.jsonl` and `data/manifest.json` copied together; the main README lists the data files in the repo layout. Where to obtain them in the current repo state `[NOT DOCUMENTED]`: check the repo at HEAD and the linked Hugging Face dataset pages, and report.

A2.3 If obtained, run the offline verifier (documented: needs no GPU and no API calls; it checks hashes, counts, and that no example or source family appears in both train and evaluation): `.venv-curator/bin/python -m nimble.training.verify_dataset`. `[DOC: N-README, N-DATASET]` The documented environment layout uses separate Python environments for MLX, PyTorch and "curator" (`requirements/`). `[DOC: N-README, Development]` The exact install commands for the curator environment `[NOT DOCUMENTED]`: read `requirements/`.

### A3. Re-implement the method for our fields

The documented steps of contrastive data curation are in `01_data_spec_and_generation.md` section 4.4 (from `[DOC: N-README]`). Implement them for our fields as described there (`[OUR DECISION]` mapping). Requirements:

- Pair edits change at most eight words in one sentence (the documented limit).
- Every model call (generation and checks) is cached with its request and response so the process is replayable offline. `[DOC: N-README]`
- The deletion check (remove each evidence element and verify the focus fact becomes unknown) is adapted: for `missing_info`, removing the slot mention must turn `present` into `missing`; removing it from an already `missing` example must not change the label.
- Keep both examples of a pair, and all examples of a family, in the same split. `[DOC: N-README]`
- Report per cell: pairs generated, pairs rejected by each check, final pairs kept.

### A4. Evaluate whether pairs help

`[OUR DECISION]` Ablation (uses the systems in files 02 and 04): train the same system with (a) unpaired data and (b) data including contrastive pairs, same total size. Nimble's authors did not run ablations of this method (they say it is "a critical piece" they believe in but did not ablate), so this is a new measurement. `[DOC: post on X by a Nimble author, search snippet]` Report per-field accuracy, ECE and Brier, and automatable share on the test set.

### A5. Checkpoint contract for Track A

Generation of pairs is long and interruptible: append finished pairs immediately to persistent storage, cache all teacher responses, keep a `STATE.json` of progress per cell and stage (generation, checks, labelling). See `00` section 5 and `01` section 8. `[OUR REQUIREMENT]`

## 5. Track B: run Nimble's trainer (conditional)

### B0. Prerequisites (all must hold; otherwise stop and report)

- A CUDA GPU with BF16 support: the documented check is `python -c 'import torch; assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()'`. `[DOC: N-README]`
- Python 3.12; the documented preparation environment installs `torch==2.8.0` and `requirements/training.txt`. `[DOC: N-README]`
- Data in Nimble's format (Track A step A2 must be complete). Nimble's loader needs `data/manifest.json`, certificates and disjoint source families. `[DOC: N-TRAIN, N-DATASET]` Whether our own data can be loaded `[NOT DOCUMENTED]`: study the loader code and write down what a minimal valid record and manifest need. If our data cannot be expressed in this format without large changes, stop.

### B1. Documented 9B command (reference only; do not run on free tiers)

`[DOC: N-TRAIN]`

```
python -m nimble.training.schema_train train \
  --model Qwen/Qwen3.5-9B \
  --revision c202236235762e1c871ad0ccb60c8ee5ba337b9a \
  --data-dir data \
  --validation data/eval.jsonl \
  --output-dir .cache/runs/nimble-9b-new \
  --learning-rate 5e-5 --lora-rank 16 --seed 17 \
  --batch-size 2 --gradient-accumulation 4 --max-length 2048 \
  --max-steps 1062 --warmup-steps 107 --save-steps 354 --stop-after-epochs 1
```

What the doc says about it: one epoch is 354 optimizer updates at effective batch size 8; it uses the previously selected three-epoch linear learning-rate schedule; the holdout is for final reporting, not for checkpoint or hyperparameter selection; changing the base model requires an explicit pinned `--revision` and tokenization is regenerated; use a fresh output directory for a new run; outputs are adapter weights, tokenizer, pinned model and prompt contract, a data audit, and before/after evaluation metrics. `[DOC: N-TRAIN]`

Note the arithmetic: 1062 = 3 x 354 and 354 = ceil(2826 / 8). `[OUR DECISION, derived from the documented numbers; verify in the code]` If our data has N examples, the equivalent would be steps per epoch = ceil(N / 8), max steps = 3 x that, save steps = steps per epoch (or smaller, see B3). Warmup 107 is about 10% of 1062; whether the code expects that `[NOT DOCUMENTED]`.

### B2. Smaller base model (exploratory)

- Documented: the base model can be changed with `--model` and an explicit `--revision`. `[DOC: N-TRAIN]` The scorer's default model when none is given is a Qwen3.5-4B baseline (MLX scorer), which shows scoring code can run on a 4B model. `[DOC: N-README]`
- Not documented: that the **trainer** works with a Qwen3.5 model smaller than 9B, and its memory use. `[NOT DOCUMENTED]` Do not assume it.
- Smoke test `[OUR REQUIREMENT]`: with a handful of examples, run the trainer with a small base (for example `--model Qwen/Qwen3.5-4B` with its pinned revision), `--max-steps 5`, and record success, peak memory and step time. If it fails, write the exact error and stop.

### B3. Checkpointing and resume (mandatory)

`[OUR REQUIREMENT]`

- `--save-steps` exists in the documented command; set it so that about 10 minutes of training are lost at worst (measure step time in the smoke test). A resume flag `[NOT DOCUMENTED]`: run `python -m nimble.training.schema_train train --help`, read the code, and write down what you find.
- The documentation says to use a fresh output directory for a new run, so resuming into an existing directory may be unsupported. If the code cannot resume, either implement resume in a wrapper or fork (log the diff) or stop; never silently restart from zero.
- Copy the latest checkpoint to persistent storage after each save.

### B4. Scoring and evaluation

- Scoring with a saved adapter: `python -m nimble.training.schema_train score --adapter <dir> --context '<text>' --schema-file examples/parallel_schema.json`. `[DOC: N-TRAIN]`
- Keep the adapter **unmerged** when scoring on CUDA (the docs describe running the adapter without merging it; merging is documented for the MLX path). `[DOC: N-README]`
- Remember temperature: the scorer applies a temperature as post-processing; loading only the LoRA weights with a plain softmax gives T=1.0. `[DOC: N-HF v2 card, search snippet]` Fit our own temperature on the calibration split (file 05).
- Evaluate with `05_evaluation_protocol.md`. Latency: the CUDA scorer processes each field with the full prompt, so measure all fields of our record in one pass.

## 6. Go/no-go summary

| Check | Pass condition | If fail |
|---|---|---|
| License (A1.2) | A license file exists and allows our use, or we only re-implement the method | Track A by documentation only |
| Data format (B0) | Our data can be expressed in Nimble's format | Stop Track B |
| BF16 GPU (B0) | check passes | Stop Track B |
| Smaller-base smoke test (B2) | runs and fits in memory | Stop Track B |
| Resume (B3) | implemented or supported | Stop Track B |

Unquantized 9B weights alone are about 18 GB `[DOC: N-README]`; training such a model on a free-tier GPU is not something the documentation covers. `[NOT DOCUMENTED]`

## 7. Deliverables

`RESULTS_NOTES.md` (license, commit, every `[NOT DOCUMENTED]` finding), `NIMBLE_FORMAT_NOTES.md`, our pair-generation spec and cached replay logs, the ablation table (A4), and, only if Track B ran, run directories with `STATE.json`, checkpoints and evaluation outputs.

## 8. Risks

- Synthetic labels were not human-reviewed in Nimble's data; ours need the verification step in file 01. `[DOC: N-README]`
- Nimble's own evaluation is narrow and its authors say there is no standard benchmark for the task. `[DOC: post on X by a Nimble author, search snippet; N-README]`
- Probability thresholds change when temperature changes; re-test thresholds after any refit. `[DOC: N-README]`
