# 10 · Sources and caveats

## Sources

| Source | What it gave | Used in |
|---|---|---|
| `IMPLEMENTATION.md` (technical spec, 13 Nov 2026, now split into these chapters) | Training data facts, builder rules, file formats, Kev and Laya trainer facts, hyperparameters, estimates, tests. Its *(repo)* facts were computed on train by its author; its *(upstream)* facts were read from `kev` `main` and `laya` `main` on 13 Nov 2026. | Chapters 02 to 09 |
| `RUNS_REPORT.md` (13 Nov 2026) | Round-1 results, dtypes, hardware, caveats. | Chapters 01, 03 |
| Baselines `01-decisions-log.md` (C-01 to C-34, L, P, X) | Round-1 decisions this round inherits. | Chapters 01 to 04 |
| Baselines `HANDOFF.md` (13 Nov 2026) | Run ids, lessons, branch and Kaggle workflow. | Chapters 03, 04 |
| Baselines handbook README | Agent rules and status tags. | README |
| Owner answers in chat, 13 Nov 2026 | All `FT-C-` decisions. | Chapter 01 |

Not read for this handbook: the upstream sources themselves, the data card, the baselines code, plans and notebooks. The owner chose to trust the spec's upstream facts (FT-C-05); chapter 09 lists the checks.

## Facts to re-check at run time

| Topic | Why |
|---|---|
| Kaggle quotas and session limits | Figures change; per account. |
| Time estimates (0.8B 30 to 60 min per epoch, 4B about 3 h per epoch, Laya about 10,000 items per epoch) | Estimates, not measurements; the pilot measures them. |
| `kev` and `laya` interfaces (`kev.train` flags, `laya.train` functions) | Read from `main` on one day; pin the exact sha and version in the run. |
| Hub revisions (tags move) | Pin commits and log `weights_sha256`. |

## Known caveats

- **Not like-for-like across models.** Fine-tuned Kev-0.8B against zero-shot Kev-4B or Kev-9B is context only (chapter 03).
- **Dtype mix inherited from round 1.** 0.8B runs fp32, 4B runs bf16 on a T4 without native bf16 (baselines C-32). Part of any size effect may be a precision effect; the report says so.
- **Latency** is comparable with zero-shot only on the same hardware, dtype and `causal_conv1d` fallback path.
- **Single run, one wording per model.** No variance across seeds; the bootstrap measures sampling noise over the test rows only, not training-seed noise. Do not read the interval as training reliability.
- **Test labels were synthetic and not hand-checked in round 1** (`verified: false`). A score of 100% is not expected. The owner chose not to carry a "draft, unreviewed" label on fine-tuning reports (FT-C-21); keep this caveat in the sources chapter of any report, since it does not go away.
- **Laya fine-tuned weights are saved as fp16** by `save_checkpoint`, while loading is fp32 on CPU; the evaluation runs fp16 on the T4, as in round 1.
- **Kev-0.8B English-only card.** Italian zero-shot was weak; a small gain after fine-tuning is a result, not a failure.
- **Class imbalance** is untreated in the first run (FT-C-10). The known weak spots (clarification precision, `lightweight` recall) may persist.
- **Prompt-injection refusal** is judged on 18 test rows; per-slice numbers move a lot between runs.

## Related project references

The project's `orchestrator_experiment_references.md` lists design choices and papers (LoRA recipe, option shuffling, per-field temperature scaling, per-question thresholds) for this stage. They inform the spec, but the decisions log is what binds the agents.
