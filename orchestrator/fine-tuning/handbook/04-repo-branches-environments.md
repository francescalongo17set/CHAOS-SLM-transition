# 04 · Repo, branches, environments

## Branch model (FT-C-17)

```
orchestrator/fine-tuning                 ← base: shared data step + this handbook
  ├── orchestrator/fine-tuning-laya      ← Laya-multilingual
  ├── orchestrator/fine-tuning-kev-0.8b  ← Kev-0.8B
  └── orchestrator/fine-tuning-kev-4b    ← Kev-4B
```

The three pipeline branches are independent and can run in parallel. The shared step (chapter 02) is merged into `orchestrator/fine-tuning` **first**, otherwise three branches invent three data builders. The baselines package on `orchestrator/baselines` is imported, never edited on these branches.

| Stage | Branch | Content |
|---|---|---|
| 0 | `orchestrator/fine-tuning` | Data builder, splitter, checks, tests (chapters 02 and 07), `data/manifest.json`, this handbook. |
| 1 | the three pipeline branches | Pipeline code, notebooks, runs. Pull shared changes from the base; never fork them. |
| 2 | `orchestrator/fine-tuning` | Merge run logs and reports back; produce the comparison. |

## Layout

```
orchestrator/
  baselines/                  # untouched here; imported as a package
  fine-tuning/
    handbook/                 # this folder
    common/                   # shared data builder, splitter, checks (chapter 02)
      build_data.py  split.py  checks.py  tests/
    kev/
      train_kev.py            # wrapper around `python -m kev.train` (chapter 06)
      calibrate_kev.py        # temperature fit (chapter 06)
      kaggle_kev_ft.ipynb     # one notebook, size chosen by a parameter (0.8b, 4b)
    laya/
      train_laya.py           # chapter 05
      kaggle_laya_ft.ipynb
    data/                     # generated, git-ignored; manifest.json committed
    runs/                     # eval logs, committed after validation
```

Rules:

- Imports follow the restructured baselines package paths (`from orchestrator.baselines.common.questions import ...`).
- `kev/` and `laya/` have **no `__init__.py`**: a package of that name would hide the upstream `kev` / `laya` library (baselines HANDOFF lesson). Scripts add `common` with `sys.path.append`.
- Heavy installs go in a separate virtual environment per pipeline (baselines C-26).
- Run logs are committed only after `validate_log` passes. The root `.gitignore` ignores `runs/`; add the same exception for `orchestrator/fine-tuning/runs/` that baselines C-31 added for its runs.
- **Weights are never committed** (FT-C-09, FT-P-06). Store the sha256 and the Kaggle Dataset name in `run.json`.

## Environments

Same as round 1.

| Pipeline | Environment |
|---|---|
| Kev | Upstream `kev` pinned at the commit used in round 1 (`2074cc4`, recorded in `kev/adapter.py`), `flash-linear-attention==0.5.2`, Python 3.12+, Kaggle T4. `causal_conv1d` is not installed (slow fallback path), so latency stays labelled "fallback". |
| Laya | `laya==0.4.31` (the round-1 version), `USE_TF=0`, Kaggle T4. |
| Shared (`common/`, tests) | `pyyaml`, `tokenizers`, `huggingface_hub`, `pytest`. Runs on a laptop, no GPU. |

## Kaggle workflow (reuse the round-1 pattern)

1. A bundle builder (the pattern of `kev/make_bundle.py`) ships `fine-tuning/` code and the generated data as a **private Kaggle Dataset**. After any code change, upload a new Dataset version. No git clone of the repo on Kaggle.
2. One notebook per pipeline with stages that stop at the first failure: smoke, pilot, full run, calibration, evaluation on validation, evaluation on test.
3. Save with "Save & Run All" so `/kaggle/working/...` is kept. Download `runs/...`, validate, commit.
4. Write results incrementally and make runs resumable (baselines chapter 07): a session can disconnect.
5. Kaggle's P100 may lack kernels in this torch build; the notebooks stop with a message. Use a T4.

## Account and quota allocation (FT-C-18, FT-P-01)

At least two Kaggle accounts exist. GPU quota and concurrent sessions are per account, so:

- Laya and Kev-0.8B take the two accounts first (priority order, FT-C-03).
- Kev-4B starts when an account is free (FT-P-01) and after Kev-0.8B has finished C0 and C1 (FT-P-02).
- Re-check the current weekly GPU limit and session length in session (chapter 09); the numbers change.
- Never run two training sessions on one account at once.

## Definition of done per pipeline

1. Smoke test and pilot done, time projection inside the time box (FT-C-13).
2. Full training run, calibration done, `train_report.json` and `run.json` complete (config, base and weights revisions, hyperparameters, temperatures, sha256 of the checkpoint).
3. Validation log and test log validated by the shared script; oracle 593/593; 0 error rows.
4. Report and comparison with the zero-shot reference, including bootstrap intervals (chapter 03).
5. Decisions log, README status line and the plan's status synced (agent rule 10).
6. Any `PENDING` item or failed check listed in the pull-request description, none silently decided.
