# 02. Experiment: Kev (zero-shot and fine-tuned)

Status: DRAFT v0.1. Read `00_overview_and_rationale.md` (rules, tags, checkpoint contract) and `01_data_spec_and_generation.md` first.

## 1. Goal

Measure how well released Kev checkpoints perform on our orchestrator fields zero-shot, then fine-tune Kev-0.8B (and Kev-4B only if a smoke test shows it fits) on our data, calibrate it, and evaluate it with the protocol in `05_evaluation_protocol.md`.

## 2. What Kev is (documented facts only)

- A family of small decision models: a LoRA adapter (rank 16) and a small "pointer head" on a Qwen base; no text is generated. `[DOC: K-README, "How It Works"]`
- Sizes: Kev-0.8B (base Qwen3.5-0.8B-Base), Kev-4B (Qwen3.5-4B-Base), Kev-9B, Kev-27B. Apache-2.0. `[DOC: K-README, Models]`
- Question types: `noul` (yes/no, returns P(yes)), `choice` (1 to 255 named options), `score` (ordered levels). Questions in one request share the text but cannot read each other. `[DOC: K-README]`
- Each checkpoint ships with a fitted temperature that the pointer head applies when the model is loaded (Kev-0.8B 2.35, Kev-4B 2.41). `KEV_TEMPERATURE=1.0` returns raw probabilities. `[DOC: K-README]`
- Training objective: cross-entropy on the correct answer; the adapter and head are trained together. `[DOC: K-README]`
- Published reference numbers (not our domain; for sanity only): on datasets never seen in training, accuracy dev/test is 0.648/0.697 for Kev-0.8B and 0.817/0.838 for Kev-4B; the share of decisions automatable at a 5% error budget is 0.14 for Kev-0.8B and 0.52 to 0.69 for Kev-4B, 9B and 27B. `[DOC: K-README, Models, "What to Expect"]`

Limits stated by the authors (design around these): the calibration is a single temperature; changing option order can change an answer; fine-tuning can make the base model worse at individual tasks; test any probability threshold on your own data. `[DOC: K-README, Limitations]`

## 3. Required reading

1. Kev README sections: "Quick Start", "Fine-Tune on Your Own Data / By Hand", "How It Works", "Training", "Benchmarks", "Serving Performance", "Limitations". `[DOC: K-README]`
2. `skills/kev-finetune/README.md` (what the fine-tune adds: accuracy on your labels and a temperature fitted to your data). `[DOC: K-FT]`
3. **Not read by the authors, read now:** `docs/model-cards/kev-0.8b.md`, `docs/model-cards/kev-4b.md`, `skills/kev-finetune/references/data-format.md`, `references/hill-climbing.md`, and the output of `python -m kev.train --help`, `python -m kev.benchmark --help`.

## 4. Important constraint on the workflow

The packaged fine-tune workflow (`scripts/kev_modal.py`, "train", "evaluate", "compare") runs on Modal, a paid service. **We do not use Modal.** `[OUR DECISION]` We use the documented "By Hand" path: `kev.train`, `kev.benchmark`, `kev.serve`. The standard-library data scripts (`convert_data.py`, `split_data.py`, `plan_size.py`, `generate_data.py`) can be run locally. `[DOC: K-FT]`

What the Modal workflow does that we must reproduce by hand: score the untouched model as a baseline, train, fit the temperature on a held-out slice, and compare raw vs calibrated results. `[DOC: K-FT]`

## 5. Steps

### Step 0. Environment and hardware smoke test

0.1 Record hardware (GPU name, memory, driver) and library versions in `RESULTS_NOTES.md`. `[OUR REQUIREMENT]`

0.2 Clone the repo and record the commit hash: `git clone https://github.com/jaredpalmer/kev.git && cd kev`. `[DOC: K-README]`

0.3 Install with uv: `uv sync --extra serve`. Python 3.12 or 3.13 is required ("torch has no wheels for 3.14 yet"). `[DOC: K-README]` How to provide Python 3.12/3.13 and uv on Colab or Kaggle `[NOT DOCUMENTED]`: check what the platform provides and report. Do not change versions silently.

0.4 Check that the GPU supports bf16 (the documented training commands use `--dtype bf16`). `[DOC: K-README]` Whether the free-tier GPU supports bf16 `[NOT DOCUMENTED]`: test with `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.is_bf16_supported())"` and write the result down. If bf16 is not supported, do not guess another dtype: run `python -m kev.train --help` and report what dtype values exist.

0.5 Run Kev's own sanity run to verify the training stack end to end: `uv run python -m kev.train --n_per_source 40 --accum 4 --out runs/smoke` (documented as about 1 minute). `[DOC: K-README, Training]` Record peak memory and seconds per step. `[OUR REQUIREMENT]`

### Step 1. Convert and validate our data

1.1 Convert the canonical records to Kev format as described in `01_data_spec_and_generation.md` section 6.1 (stage A and stage B records). `[OUR DECISION]`

1.2 Validate and split with `scripts/split_data.py` (it validates records and splits by state; `--holdout` accepts a separate real file). `[DOC: K-FT]` Keep our own splits (train / calibration / test) from file 01; use `split_data.py` only for validation unless its split matches ours. Check that the count of valid records equals the count written (Kev issue about U+2028/U+2029/U+0085, see file 01 section 7). `[OUR REQUIREMENT]`

1.3 If the validator rejects records with different question sets per record, report the exact message and use the fallback described in file 01 section 6.1. `[NOT DOCUMENTED]`

1.4 Check dataset size with `scripts/plan_size.py` (documented: about 1,000 records for three questions per record to measure a +5 point gain; with 400 records the gain was inside the noise). `[DOC: K-FT]`

### Step 2. Zero-shot baseline of released checkpoints (no training)

2.1 Pin the weights with the documented tag syntax: `--run jaredpalmer/kev-0.8b@v1.0` (each Hub repo has a `v1.0` tag). `[DOC: K-README, "Kev 1.0"]` The `@tag` syntax is documented for `kev.serve`; whether `kev.benchmark --run` accepts it `[NOT DOCUMENTED]`: test it, and if it fails use the Hub revision hash from the Kev 1.0 table (0.8B: `9a45d25e`, 4B: `139fdd94`) `[DOC: K-README, "Kev 1.0"]` or a local download.

2.2 Score the calibration and test files:

```
uv run python -m kev.benchmark --run jaredpalmer/kev-0.8b@v1.0 --data <our_file>.jsonl --out runs/kev08-zeroshot
```

The command pattern (`--run`, `--data`, `--out`) is documented for a fine-tuned run; using a released checkpoint with `--run` is documented for suites. `[DOC: K-README, Benchmarks]` The report contains accuracy, Brier score, calibration error, the share of decisions that can be automated at a 5% error budget, option-order changes and question isolation. `[DOC: K-README, Benchmarks]` The `--allow-test` flag in the documentation refers to Kev's own suites, so what it means for our files `[NOT DOCUMENTED]`; do not use it unless the tool demands it, and report if it does.

2.3 Repeat for `jaredpalmer/kev-4b@v1.0` only if the hardware can run it (serving 4B on CUDA is documented for L40S and H100 `[DOC: K-README]`; a smaller GPU is `[NOT DOCUMENTED]`: test and report).

2.4 Save the result files to persistent storage.

### Step 3. Fine-tune Kev-0.8B

3.1 Documented starting command (shown for Kev-4B; `--init_from` is documented as the way to keep what Kev already knows, and a fine-tune from the plain base scored far worse in the authors' example: 0.33 vs 0.84 on Kev's own evaluation set): `[DOC: K-README, "By Hand"]`

```
uv run python -m kev.train --data train.jsonl --base Qwen/Qwen3.5-4B-Base --init_from jaredpalmer/kev-4b \
    --epochs 2 --lr 2e-5 --batch 1 --accum 8 --dtype bf16 --checkpointing 1 --device cuda --out runs/mine
```

`[OUR DECISION]` For Kev-0.8B substitute `--base Qwen/Qwen3.5-0.8B-Base --init_from jaredpalmer/kev-0.8b`. These names come from the models table `[DOC: K-README]`; the substitution itself is ours.

3.2 Rules stated by the docs: use a smaller learning rate than the from-scratch recipe (`2e-5` is a good start); pick `--base` to match the checkpoint you start from; the trainer checks that base, revision, LoRA rank and head size agree before loading. `[DOC: K-README]` Whether the 0.8B fine-tune needs an explicit `--base_revision` `[NOT DOCUMENTED]`: the first-stage 0.8B command in the README shows `--base_revision dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68`, but the fine-tune example does not; read the 0.8B model card and `--help`.

3.3 Memory: `--batch 1 --accum 8` in bf16 fits the 0.8B model on a 4 GB GPU. `[DOC: K-README]` Do not change these unless the smoke test fails; if it fails, report before trying anything undocumented.

3.4 Options seen but not explained: a Kev-9B model card snippet shows a fine-tune with `--replay 2000`. `[DOC: K-HF-9B, snippet]` Its meaning `[NOT DOCUMENTED]`: read `--help`. Do not use it before you understand it.

3.5 **Checkpointing and resume (mandatory, see `00` section 5).** `[OUR REQUIREMENT]`

- Intermediate saves and resume in `kev.train` `[NOT DOCUMENTED]`. First inspect `--help` and `kev/train.py`.
- If it supports periodic saves and resume: use them, with the cadence from the smoke test.
- If it does not: do one of the following, record which, and keep the upstream code unchanged in a fork or wrapper (log the diff):
  - (a) Patch the trainer to save adapter, head and optimizer state every N steps and to resume. Apache-2.0 allows modification. `[DOC: K-README, License]`
  - (b) Split training into one-epoch stages chained with `--init_from` (Kev's own follow-up fine-tunes are chained through the same path `[DOC: K-README, Training]`). Whether `--init_from` accepts a local checkpoint directory `[NOT DOCUMENTED]`: test it. Chaining restarts the learning-rate schedule and drops optimizer state; note this deviation in the results.
- Save the adapter and head to persistent storage after every epoch at minimum; keep `STATE.json` current.

3.6 Kev records the checkpoint a run started from in `runs/<name>/training_config.json`. `[DOC: K-README]` Keep this file with the results and add our config hash, data hashes and commit hashes.

3.7 Run one epoch on a small subset first (smoke test), then the full run. Log training loss every N steps to a file on persistent storage.

### Step 4. Calibration

4.1 What is documented: the temperature is stored with the checkpoint and applied at load time; the authors fitted it with `scripts/calibrate_checkpoint.py`, which also reports an out-of-fold estimate to check the in-sample fit; the released 4B and 0.8B temperatures were fitted on in-distribution development sets. `[DOC: K-README, Benchmarks]` The packaged fine-tune workflow fits the temperature on a held-out slice. `[DOC: K-FT]`

4.2 `[OUR DECISION]` Fit the temperature on our **calibration** split (never on test). How to run it `[NOT DOCUMENTED]`: read `scripts/calibrate_checkpoint.py` and its `--help`, then report the exact invocation.

4.3 Compare calibration error and Brier on the test set with the fitted temperature and with `KEV_TEMPERATURE=1.0` (raw). `[DOC: K-README, API table]` Report both.

### Step 5. Evaluation

5.1 Run the benchmark on the test set for: Kev-0.8B zero-shot (step 2), Kev-0.8B fine-tuned (step 3 + 4). Follow `05_evaluation_protocol.md` (per-field metrics, sensitive-feature recall, Italian slice, automatable share).

5.2 Option-order robustness: use `POST /v1/systemone/permute` (runs one choice question with different option orders; `n_perm` from 1 to 64, default 6). `[DOC: K-README, API]` Report how often the answer changes. Do this at least for `feature_classification` and the slot questions.

5.3 Latency: start `uv run --extra serve python -m kev.serve --run runs/<name> --port 8009` `[DOC: K-README]`; the API returns `latency_ms` (model time; network time is extra `[DOC: K-README, Serving Performance]`). Measure on our own request shape: stage A (3 questions) and stage B (2 to 3 slot questions), new text and the same text again (the server caches the text `[DOC: K-README]`). Report p50 and p95, the GPU used, and the dtype. For reference, the authors report Kev-4B six questions on short text in 18.1 ms on an H100 and 41.5 ms on an L40S, and 0.8B in 22.7 ms on an L4. `[DOC: K-README]` Free-tier GPU numbers `[NOT DOCUMENTED]`.

5.4 Precision: the server runs bf16 on GPUs; its probabilities differ from the fp32 evaluation path by at most about 0.03 and the top answer changes on about one question in 300. `KEV_DTYPE=fp32` selects the exact path. `[DOC: K-README, Serving Performance]` Report which one your numbers use.

5.5 Thresholds: choose per-field thresholds on the calibration split and report on test (see file 05). The Kev authors caution that a probability threshold must be tested on your own data. `[DOC: K-README, Limitations]`

### Step 6. Optional: Kev-4B

Go/no-go rules `[OUR DECISION]`:

6.1 Run step 0.5 and a 50-record version of step 3 with `--base Qwen/Qwen3.5-4B-Base --init_from jaredpalmer/kev-4b`. Record peak memory and step time.

6.2 If it runs without errors and the projected full-run time fits in the number of sessions the team accepts, continue with the same checkpoint contract. If it runs out of memory, stop and report. Do not try quantization or other memory tricks: they are `[NOT DOCUMENTED]` for Kev's trainer; ask the team first.

6.3 Documented context: a Kev-4B first-stage training run is about 1 hour on one H100, and CUDA GPUs listed for 4B are L40S and H100. `[DOC: K-README]`

## 6. Deliverables

On persistent storage, under `runs/`:

- `RESULTS_NOTES.md`: hardware, versions, commit hashes, every `[NOT DOCUMENTED]` finding with what you checked.
- For each run: `training_config.json`, `STATE.json`, training log, final adapter and head, fitted temperature.
- Benchmark outputs for zero-shot and fine-tuned runs; the permute and latency measurements.
- A filled table following `05_evaluation_protocol.md`.

## 7. Known risks

- Fine-tuning in-distribution gains do not predict performance elsewhere; the authors state their reported gains are in distribution. `[DOC: K-README]`
- Kev-0.8B is much weaker than the larger models on unseen sources (see section 2). Expect to need the fallback ladder for low-confidence cases.
- Italian: no evidence in the docs. Report the Italian slice separately.
- Kev's data scripts have a known line-splitting issue (file 01 section 7).
