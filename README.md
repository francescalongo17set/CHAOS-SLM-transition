# Insurance-law orchestrator: routing baseline with a real decision model

For each user query the orchestrator asks three typed multiple-choice questions and applies thresholds in plain code. It never answers the query and never reads documents.

| Decision | Choices | Used for |
|---|---|---|
| safety | safe / unsafe | **stop** if P(unsafe) ≥ t_unsafe |
| scope | in_scope / out_of_scope | **stop** if P(out_of_scope) ≥ t_scope |
| complexity | lightweight / agentic | **lightweight** only if P(lightweight) ≥ t_light, else **agentic** |

Each decision is `{decision, probability, alternatives}`. Order: safety, scope, complexity. All three thresholds are tuned on the calibration split.

**Complexity definition:** *lightweight* = one lookup (a definition, a deadline, one provision). *agentic* = multi-step (compare provisions or policies, apply rules to a scenario, calculate, draft a document).

## The decision model

**Laya-multilingual** ([model card](https://huggingface.co/convaiinnovations/laya-multilingual), Apache-2.0): a 322M encoder (mmBERT) with a trained decision head. It reads the text once and outputs a probability per option; it generates no text and has no LLM inside. It is near chance until fine-tuned (its own card says so), so we fine-tune it on our labels on Kaggle. Italian is not named on its card; the evaluation tells us. `orch/backends.py` is the only place that touches Laya, behind the `DecisionBackend` interface, so the real Jev API or another model can replace it without touching `router.py`.

Why not the others: Jev is a closed paid API (no confirmed free tier); Von is English-only and archived; Kev is a Qwen LLM with a decision head (runner-up if an LLM body is acceptable).

## Layout

```
orch/decision.py   Decision envelope, DecisionBackend interface, the 3 questions
orch/backends.py   LayaBackend
orch/laya_data.py  our labels -> Laya's fine-tuning JSONL
orch/router.py     Thresholds, route(), Orchestrator + JSONL decision log
orch/evalkit.py    metrics, threshold tuning, sweep, knee, plot (pure python)
scripts/           build_corpus -> gen_queries -> split -> train_laya -> run_eval, make_kaggle
tests/             unit tests (run in CI, no GPU)       .github/workflows/tests.yml
```

## Data (v2)

About 3,000 synthetic queries (Qwen2.5-7B-Instruct writes them from the insurance texts, Italian ~60% / English ~40%), labelled by construction, split **by source passage** so the test set holds passages and topics the model never saw:

| Split | Use |
|---|---|
| train (~70%) | fine-tune Laya |
| calib (~15%) | tune the three thresholds |
| test (~15%) | final numbers, read only |
| gold (50, subset of test) | editable CSV for hand-checking |

Cells: in-scope lightweight / agentic, out-of-scope non-legal, out-of-scope legal (ITA-CaseHold seeds), and four unsafe kinds (injection, fabricated claims, forged documents, personal-data fishing). Licences: `DATA_SOURCES.md`. The first 300-query set (`data/v1`) is kept only as history.

## Run on Kaggle

Prereqs: the Kaggle CLI logged in with an API token (`~/.kaggle/access_token`), phone-verified account (GPU and internet). Replace `<user>` with your Kaggle username.

**1. Build and upload the code**
```bash
KAGGLE_USER=<user> python scripts/make_kaggle.py
```
```bash
kaggle datasets version -p dist/code -m "laya" -r zip
```

**2. Generate the data (about 1.5 to 2.5 hours, resumable)**
```bash
kaggle kernels push -p dist/01-data
```
```bash
kaggle kernels status <user>/orchestrator-01-data
```
```bash
kaggle kernels output <user>/orchestrator-01-data -p kaggle_out3
```
```bash
mkdir -p data && cp -r kaggle_out3/out/v2 data/v2
```
Check `kaggle_out3/out/gen_report.json` (cells near quota?) and `data/v2/manifest.json` (train/calib/test sizes).

**3. (Optional) hand-check `data/v2/gold.csv`**, then upload the data:
```bash
echo '{"title":"orchestrator-data-v2","id":"<user>/orchestrator-data-v2","licenses":[{"name":"other"}]}' > data/v2/dataset-metadata.json
```
```bash
kaggle datasets create -p data/v2
```

**4. Smoke test (about 5 to 10 minutes). Do this before the long run.**
```bash
kaggle kernels push -p dist/02-smoke
```
```bash
kaggle kernels status <user>/orchestrator-02-smoke
```
It proves Laya's training format, fine-tune call and loading work. If it fails, send me the error.

**5. Full fine-tune + evaluation (about 1 to 2 hours)**
```bash
kaggle kernels push -p dist/03-train
```
```bash
kaggle kernels output <user>/orchestrator-03-train -p kaggle_out4
```
**Copy back:** `kaggle_out4/runs/finetuned/` (metrics.json, cost_vs_accuracy.png, sweep_calib.csv, decision_log.jsonl), `runs/untrained/` (the untrained reference) and `mlflow.db`. The fine-tuned model is in `laya_ft/` in the notebook output.

Not run by me: everything on Kaggle. The Laya calls follow its documented API but were only tested against a stand-in object here, which is why the smoke test exists.

## Evaluation

Stop thresholds are chosen on **calib**: best route accuracy among settings that still catch at least 90% of unsafe queries (`--target-recall`). Then the complexity threshold is swept (cost vs accuracy) and the knee (best point among settings nothing else beats on cost and accuracy) is taken. Test and gold only report. Cost: lightweight = 1, agentic = 5, stop = 0 (`--agentic-cost`).

| Metric | Meaning |
|---|---|
| `acc_safety / acc_scope / acc_complexity` | accuracy of each decision after thresholds (complexity only on in-scope safe rows) |
| `acc_route` | the final route matches the gold route |
| `false_escalation` | easy queries sent to agentic (wasted cost) |
| `false_lightweight` | hard queries sent to lightweight (quality risk) |
| `safety_recall` | unsafe queries that end in **stop** |
| `false_block` | normal queries wrongly stopped |
| `cost` | mean cost units per query |

## MLOps

- **MLflow:** params, metrics and artifacts per run in a local SQLite file `mlflow.db` (`mlflow ui --backend-store-uri sqlite:///mlflow.db`). The plain-folder `mlruns/` store is refused by the current MLflow release, so SQLite is the same idea: one local file, no server.
- **Dataset versioning:** plain versioned folders (`data/v2/`) with a SHA-256 manifest, no DVC. Files are small, no remote to set up, and every MLflow run logs the hash of the exact files it used.
- **Decision log:** `decision_log.jsonl`, one line per routed query: query, each decision with probability, thresholds, route, reason, model name and weights hash. `Orchestrator(backend, log_path=...)` writes the same format in use.
- **CI:** `.github/workflows/tests.yml` runs `pytest`. No GPU, no model download, no Laya install.

## Things to know

- Labels are **by construction**, written by Qwen from the recipe. Gold is meant for a hand-check, but numbers against unchecked labels show direction, not exact accuracy.
- The unsafe share (about 27%) is far higher than real traffic. Accuracy numbers will not carry over unchanged.
- Laya has no documented resume for training; it saves `checkpoint_latest/` each epoch, but an interrupted run is simplest to restart.
