# 00. Orchestrator experiments: overview and rationale

Status: DRAFT v0.1, 3 Nov 2026. Read this file first. It explains what we are building, why we chose these experiments, the hardware limits, and the rules every coding agent must follow.

## 0. Rules for coding agents (read before doing anything)

1. **Do not infer.** Every instruction in files 01 to 05 carries a provenance tag:
   - `[DOC: <source id>]`: stated in a repo, model card or paper listed in section 7. You may rely on it.
   - `[OUR DECISION]`: a team choice. You may follow it, and you may propose changes, but never present it as a fact about a repo.
   - `[OUR REQUIREMENT]`: a mandatory rule we impose (mostly checkpointing and logging).
   - `[NOT DOCUMENTED]`: the documentation we read does not say. **Do not guess.** Run the tool's `--help`, read its source code, or run a small test, then write the finding in `RESULTS_NOTES.md` (what you checked, what you found, the commit hash or version).
2. If a documented command fails on our hardware, stop, write down the exact error in `RESULTS_NOTES.md`, and try only the fallbacks that the file allows. Do not invent flags.
3. Before implementing any experiment, read the "Required reading" documents of that file. We (the authors of these files) read only the READMEs and a few docs. The sources we did **not** read are listed in section 7.
4. Pin versions: record the git commit hash of every repo and the Hub revision of every model you use, in the run's config file. `[OUR REQUIREMENT]`
5. Costs are out of scope for now (team decision). Report latency, call counts and escalation rate instead. `[OUR DECISION]`

## 1. What we are building

The orchestrator is the first step in the pipeline. For each user request it outputs one record:

| Field | Meaning | Produced by |
|---|---|---|
| `safety_check` | safe or not | a teammate's component (out of scope here; keep the same `{label, confidence}` interface) |
| `scope_check` | `in_scope`, `out_of_scope`, `quick_reply` | our model |
| `feature_classification` | one of 5 features, or `none` | our model |
| `complexity_estimation` | `simple` or `complex` | our model |
| `missing_info` | list of required slots that are missing or ambiguous | our model |
| `confidence` | per field and overall | derived from the model's probabilities |

`[OUR DECISION]` The five features are: regulatory consultation, product and policy analysis, comparison, IBIP screening, client drafting. Slot lists per feature are illustrative and must be aligned with the Lightweight and Agentic designs (open point).

## 2. Decision from the mentor meeting

Little time for experiments, so we skip rules and classical ML and focus on robust models: either one SLM that produces the whole record, or "decision models" (Jev-style) that return a probability distribution over fixed options with no text generation. The word "Jev" here means this pattern, not the hosted product. `[OUR DECISION, from team notes]`

Also decided: training runs on Colab and/or Kaggle free tiers; starting from released decision-model checkpoints (Kev) is acceptable. `[OUR DECISION, from team notes]`

## 3. The experiments and why

| File | System | Why it is in the plan |
|---|---|---|
| `02_exp_kev.md` | Kev (Jev-style decision model, open weights) | Documented fine-tuning path; training data format is close to our record; 0.8B variant is documented to train on a 4 GB GPU `[DOC: K-README]` |
| `03_exp_nimble.md` | Nimble (recipe + data method) | Its contrastive data curation is the most transferable idea; its 9B trainer is probably too large for our hardware, so the file separates "adopt the method" from "attempt the trainer" |
| `04_exp_own_baselines.md` | S1 generative, S2 letter-readout (ours) | Own designs, grounded in the LLM-as-Jev paper, so we control the comparison and have a baseline that does not depend on a repo |
| `05_evaluation_protocol.md` | all | One protocol for all systems so numbers are comparable |

NanoJev was reviewed and excluded: its data and training pipeline are built around game tasks (ViZDoom, Maze, Snake) `[DOC: NJ-README]`.

**Systems compared** (all on the same data and test set):

- S1: one SLM generates the full record as constrained JSON. `[OUR DECISION]`
- S2-zero: decision readout on a plain instruct/base model, no training. `[OUR DECISION]`
- S2-LoRA: S2 with a LoRA fine-tune. `[OUR DECISION]`
- Kev-0.8B zero-shot and fine-tuned; Kev-4B only if a smoke test shows it fits. `[OUR DECISION]`

## 4. Evidence behind the main choices (what papers and repos actually say)

- A frozen LLM can act as a decision model: score the options from next-token probabilities. On Qwen3.5-4B the training-free readout scored 81.4% on the paper's benchmark, equal to the same model generating text (81.4%). The practical gain is no decoding and free probabilities. `[DOC: P1 Table 1]`
- A readout needs one prefill plus about 2 sequential forward passes; thinking variants need hundreds to thousands. `[DOC: P1 Table 17]`
- Fine-tuning helps small models and in-domain tasks most. For a 4B model gains are mostly in-domain. `[DOC: P1 §4.3]`
- Training on one task format biased the model: intent-only data pushed "yes" predictions up and raised ECE from 0.057 to 0.134. Balanced formats fixed it. `[DOC: P1 App. G]`
- Zero-shot routing between cheap and strong LLMs was at chance for both decision models tested. Our `complexity_estimation` is a routing-type decision, so do not rely on zero-shot. `[DOC: P3 §5]`
- Decisions about whether to act, and clarification, are harder to delegate than choosing among options (98.4% vs 52.0%; clarification replaced only 28% of the time). `missing_info` is our clarification-type decision. `[DOC: P4 §5.4, Table 2]`
- Kev: fine-tuning on about 1,050 generated records improved accuracy from 67.7% to 73.6% on an example workload; with 400 records the gain was inside the noise. `[DOC: K-FT]`
- Option order can change an answer even though questions are isolated. `[DOC: K-README, Limitations]`
- Confidence thresholds picked on the data they are measured on hide misses; use a separate calibration split. `[DOC: P3 §6]`

## 5. Hardware limits and the checkpoint contract (applies to every experiment)

Training happens on Colab and/or Kaggle free tiers. We do not know the session limits or quotas and we must not assume them. `[OUR DECISION]` Therefore every experiment must satisfy this contract. `[OUR REQUIREMENT]`

1. **Assume interruption at any time.** Sessions can end without warning. No result may live only in notebook memory or in the session's local disk.
2. **Persistent storage.** Write checkpoints, logs, configs and results to storage that survives the session (for example, a mounted Google Drive on Colab, or Kaggle's persistent output mechanism). The agent must verify how persistence works on the platform in use and note it in `RESULTS_NOTES.md`.
3. **Checkpoint cadence.** Save a checkpoint at the end of every epoch and also every N optimizer steps. Measure the seconds per step in the smoke test (item 6) and choose N so that about 10 minutes of training are lost at worst. If the training tool has its own save option, use it; otherwise add it.
4. **Resumability.** Every training and evaluation script must be resumable: write a `STATE.json` (last completed step or epoch, seed, config hash, data file hash, commit hashes), and on start read it and continue. A re-run must never silently restart from zero.
5. **Atomic writes.** Write checkpoints to a temporary name and rename when complete, so a session ending mid-write cannot corrupt the latest checkpoint.
6. **Smoke test first.** Before any real run, run a tiny version (a few dozen examples, a few steps). Record: GPU name and memory, peak memory, seconds per step, and whether the dtype in the command works on this GPU. Stop and report if it fails; do not start the long run.
7. **Log the hardware** (GPU model, memory, driver, library versions) at the start of every run, and store it with the results. Latency numbers are only meaningful with the hardware named.
8. **Keep three things always up to date on persistent storage:** the latest checkpoint, `STATE.json`, and the training log.
9. **Lost-work report.** When resuming, log how many steps were redone.
10. **One experiment at a time on one GPU.** `[OUR DECISION]`

What the repos document about this: Kev's README shows no resume option and says nothing about Colab or Kaggle `[NOT DOCUMENTED]`; Nimble's training command includes `--save-steps` `[DOC: N-TRAIN]` but a resume flag is not shown `[NOT DOCUMENTED]`, and the doc says to use a fresh output directory for a new run `[DOC: N-TRAIN]`. The agent must check each tool's `--help` and source before deciding how to implement resume.

Known hardware facts from the docs (do not extend them):

- Kev-0.8B: `--batch 1 --accum 8` in bf16 fits a 4 GB GPU `[DOC: K-README]`. Kev-4B: CUDA GPUs listed are L40S and H100 `[DOC: K-README, Models table]`; training memory for 4B on small GPUs `[NOT DOCUMENTED]`.
- Nimble CUDA path requires a GPU with BF16 support `[DOC: N-README]`; the 9B weights alone are about 18 GB unquantized `[DOC: N-README]`.
- Whether the free-tier GPU supports BF16 is not documented anywhere we read. Test it in the smoke test. `[NOT DOCUMENTED]`

## 6. How the files fit together

1. `01_data_spec_and_generation.md`: the record format, label spaces, how to generate, verify, split and convert data. All experiments consume the data produced there.
2. `02_exp_kev.md`, `03_exp_nimble.md`, `04_exp_own_baselines.md`: experiments, each with numbered steps and its own checkpoint section.
3. `05_evaluation_protocol.md`: metrics, thresholds, latency, reporting table. All systems are evaluated the same way.

Suggested order: 01, then 04 (S2-zero baseline needs no training), then 02 (Kev-0.8B), then 03 (method adoption), then optional heavy items. `[OUR DECISION]`

## 7. Sources

Read in full or in part by the authors of these files:

| ID | Source | Notes |
|---|---|---|
| K-README | https://github.com/jaredpalmer/kev (README.md) | Read in full |
| K-FT | https://raw.githubusercontent.com/jaredpalmer/kev/master/skills/kev-finetune/README.md | Read in full. Its workflow runs on Modal (a paid service); we do not use Modal, only the data scripts and ideas |
| K-ISSUE276 | https://github.com/jaredpalmer/kev/issues/276 | Search snippet only |
| K-HF-9B | https://huggingface.co/jaredpalmer/kev-9b | Search snippet only |
| N-README | https://github.com/bespokelabsai/nimble (README.md) | Read in full |
| N-TRAIN | https://github.com/bespokelabsai/nimble/blob/35fe1f4fdbc64fa3dbbf5ac0042f3f5680c1ad28/docs/NIMBLE_TRAINING.md | Read in full |
| N-DATASET | https://github.com/bespokelabsai/nimble/blob/35fe1f4fdbc64fa3dbbf5ac0042f3f5680c1ad28/docs/DATASET.md | Read in full |
| N-HF | https://huggingface.co/bespokelabs/Bespoke-Nimble-9B | Search snippet only |
| NJ-README | https://github.com/TianyuCodings/NanoJev | README read |
| P1 | LLM-as-Jev, arXiv 2610.02076 | Read in full |
| P2 | Evaluating and Benchmarking Jev, arXiv 2609.37647 | Read in full |
| P3 | Fast Models, Slow Evidence, arXiv 2610.02267 | Read in full |
| P4 | REFLEX with Jev, arXiv 2609.26532 | Read in full |

**Not read (agents must read these before the steps that depend on them):**

- Kev: `skills/kev-finetune/references/data-format.md`, `data-generation.md`, `hill-climbing.md`, `SKILL.md`, `docs/model-cards/kev-0.8b.md`, `kev-4b.md`, `PLAN.md`, `kev/train.py` options (`--help`).
- Nimble: `docs/TRAINING_EVAL_CURATION.md`, `docs/PARALLEL_SCORING.md`, `docs/PUBLIC_BENCHMARKS.md`.
- System1-Arena (https://arxiv.org/abs/2610.21244), referenced by NanoJev: not opened.

**Licenses:** Kev is Apache-2.0 `[DOC: K-README]`. NanoJev is MIT `[DOC: NJ-README]`. Nimble: no license is stated in the README we read; third-party pages disagree (one reports no license file, another reports Apache 2.0). **Unverified: check the repo's LICENSE file before copying any Nimble code.** Training datasets used by released models have their own licenses `[DOC: K-README, License]`.

**Related files made earlier (our drafts, not run against a real model):** `orchestrator_data.py`, `orchestrator_readout.py`, `orchestrator_experiment_references.md`.
