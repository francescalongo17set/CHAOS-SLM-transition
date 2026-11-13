# Plan P1 · Kev-0.8B

Branch: `orchestrator/baselines-kev-0.8b` (created from `orchestrator/baselines` at d56311c). Larger sizes later on `-4b` / `-9b` (C-27).
Status: **Kev-0.8B DONE, validated** (12 Nov 2026; run `kev-0.8b-20261112-a`, logs in `runs/kev/`, commit 2ef76ac; test route accuracy 0.331, see `report_test.md`). 4B and 9B not started. History: Code and Kaggle notebook written (`kev/adapter.py`, `run.py`, `tokens_check.py`, `make_report.py`, `kaggle_kev_0.8b.ipynb`, `tests/test_adapter.py`). Platform: Kaggle (owner). **Smoke test PASSED on a Kaggle T4** (5 rows, 0 validator problems; token finding in chapter 08); full validation and test runs completed afterwards, validator clean. Revision question resolved 13 Nov (weights identical in all three commits, chapter 12; notebook now pins `9a45d25e…`, `run.json` records `weights_sha256`). Still open: decide whether to install `causal_conv1d` before any latency comparison. Adapter tests are written but skip locally without `pydantic` + upstream `kev` on the path (they run inside the notebook's venv).
Defaults taken for §3 questions 1-2 (owner has not objected; override any time): in-process = `Checkpoint.load` with upstream `LoadOptions()` defaults, which are already **fp32, eager, no CUDA graphs, no fused kernels** (the path every upstream reported number uses), then `admit` + `model.probs` per row; two calls per row (core questions, then predicted-feature slots).

## 1. Goal and scope

Run Kev-0.8B zero-shot on the validation (298) and test (593) splits of `router.jsonl`, writing chapter-06 logs and the shared report. Relies on C-01, C-05, C-07, C-10, C-12, C-15, C-21 to C-26, L-01, L-02c, P-02, P-03, P-04, P-08 (chapters 03, 05, 06, 08).

## 2. Inputs

- Data: `data-generation/data/final/{validation,test}/router.jsonl` via `common/data.py`.
- Model: `jaredpalmer/kev-0.8b` (Qwen3.5-0.8B-Base + LoRA r16 + pointer head). Pin the Hub revision or tag (`v1.0` per README, **unverified**) and log it.
- Code: Kev repo at commit `2074cc4` (shallow-cloned 12 Nov 2026 to inspect the API; pin the same sha in `run.json.libraries.kev`).
- Environment: own venv/notebook (C-26), Python 3.12, `uv`, torch, `flash-linear-attention` on CUDA. Kaggle or Colab free GPU. Secrets: none expected (`HF_TOKEN` by name only if the repo is gated).

## 3. Open items

- **PENDING touched:** none. X-04 and X-05 are not used (probabilities are logged in full).
- **PROPOSED adopted:** P-01, P-02, P-03, P-04, P-07, P-08, P-09, P-11.
- **Owner questions raised by this plan (not decisions I may take):**
  1. **In-process call shape.** `serve.py` loads with `ck.load(dev, LoadOptions)` and runs `admit()` then `model.probs...` inside a `Server` thread with a prefix cache, CUDA graphs and fused kernels. For C-24 I propose the in-process path = `checkpoint.load` + `kev.model.admit` + `DecisionModel.probs(enc)` with **serving defaults for dtype/graphs/fused as the README documents**, batch size 1, one record per row. Confirm, or ask for the plain eager path.
  2. **dtype on T4.** Serving default is bf16; handbook P-09 and README suggest `fp32` on a T4 (no native bf16). Proposal: run fp32 (exact path) and say so; if the GPU supports bf16 (L4, A100) still use fp32 for round 1 so sizes compare like for like.
  3. **Prefix cache.** Each row has a distinct state, so the cache gives no cross-row gain; within a row the state is shared across the question rows anyway. No action unless you disagree.

## 4. Steps

| # | Step | Files | Command | Check (can fail) |
|---|---|---|---|---|
| 1 | **Smoke test.** Install Kev, load Kev-0.8B, answer the README example. Log versions, device, dtype, `torch.cuda.is_bf16_supported()`. | `kev/smoke.ipynb` (or `kev/smoke.py`) | `uv sync --extra serve` then run | One answer with probabilities summing to 1; version/device block printed. |
| 2 | **Read the source and write the call down** (ch. 08 requirement): `kev/checkpoint.py` (`load`, `LoadOptions`), `kev/model.py` (`admit`, `probs`), `serve.py` helpers `to_record` / `to_answers`. | notes in `kev/NOTES.md` | none | Call sequence reproduces step 1's answer in-process (same probs within 1e-3). |
| 3 | **Adapter** `kev/adapter.py`: canonical state + `questions.en.yaml` → Kev record; Kev probabilities → canonical `answers` with `option_order`. Slot questions for the predicted feature (C-23); `needs_clarification` per chapter 03. | `kev/adapter.py`, `kev/tests/test_adapter.py` | `pytest` | 5 hand-picked rows, one per route (ids from `audit/audit_report.md`); probs sum to 1; slot keys match `slots.by_feature`. |
| 4 | **Token accounting.** Run one row with 1 and with 4 questions, compare `tokens` returned. Decide `input_tokens_native` (state once + question rows if cache reuse). Fill `input_tokens_ref` with `common/tokens.py`. | `kev/tokens_check.py`, finding in `run.json.notes` | — | Finding written; `input_native` is not null on any row. |
| 5 | **Runner** `kev/run.py`: iterate rows, time each row end to end with `perf_counter` (cuda synchronize), batch 1, first 10 rows `is_warmup`, append+flush via `LogWriter`, resume by `query_id`, errors logged as rows (C-10, P-03). Writes `run.json` incl. `temperature_applied` from the checkpoint head, dtype, GPU, peak mem, load time, params, disk size. | `kev/run.py`, `runs/kev/<run_id>/` | `python -m kev.run --split validation --limit 50` | 50-row pilot passes `validate_log` (limit mode checks the subset); 0 silent gaps; any 422 listed. |
| 6 | **Full runs** validation then test. | `runs/kev/<run_id>/{validation,test}.jsonl`, `run.json` | `python -m kev.run --split ...` | `common.logs.validate_log` passes on both splits. |
| 7 | **Report** with the shared script. | `report.md`, `metrics.json` | `common/report.py` | Report generated; header shows dtype, GPU, revision, latency mode `in_process`. |
| 8 | **Docs sync** (rule 10): update status lines, decisions log if the owner answers §3, chapter 08 with the verified call and token finding; grep old wording. | handbook | `grep -rn` | Report of what was updated. |

## 5. Time boxes

Install + smoke: 45 min; if `flash-linear-attention` or torch will not install on the free tier, stop and report (no fallback to a different model). Full test split at about 1 s/row should fit one session; resume handles disconnects.

## 6. Failure handling

README/package mismatch, an unexpected 422, or a state above the 8,192-token validated context → log, stop, `BLOCKED` to the owner (chapter 08 triggers). No retry loops against Kaggle/Colab quota; no money (C-12). Weak Italian accuracy is a result, not a bug.

## 7. Outputs

`orchestrator-baselines/kev/*`, `runs/kev/<run_id>/*`, this plan. Weights and caches are git-ignored. Logs committed only after the validator passes.

## 8. Definition of done

Chapter 07 list: smoke on 5 rows, 50-row pilot with latency/tokens/memory, full validation and test validated, `report.md` + `metrics.json` generated, `run.json` complete with notes, open questions listed in the PR. Then repeat steps 5–7 on `-4b` and `-9b` if they fit (C-25, P-10).
