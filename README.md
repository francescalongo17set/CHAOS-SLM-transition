# Insurance-law orchestrator

[![tests](https://github.com/francescalongo17set/CHAOS-SLM-transition/actions/workflows/tests.yml/badge.svg)](https://github.com/francescalongo17set/CHAOS-SLM-transition/actions/workflows/tests.yml)
[![train-and-promote](https://github.com/francescalongo17set/CHAOS-SLM-transition/actions/workflows/pipeline.yml/badge.svg)](https://github.com/francescalongo17set/CHAOS-SLM-transition/actions/workflows/pipeline.yml)

Routes each user query to **stop**, **lightweight** or **agentic** before anything expensive runs. It never answers the query.

A small fine-tuned decision model ([Laya-multilingual](https://huggingface.co/convaiinnovations/laya-multilingual), a 322M encoder, no LLM, no text generation) answers three questions with probabilities; plain code applies thresholds:

| Question | Choices | Rule |
|---|---|---|
| safety | safe / unsafe | **stop** if P(unsafe) ≥ `unsafe` |
| scope (Italian insurance law?) | in_scope / out_of_scope | **stop** if P(out_of_scope) ≥ `out_of_scope` |
| complexity | lightweight / agentic | **lightweight** only if P(lightweight) ≥ `lightweight`, else **agentic** |

*lightweight* = one lookup (a definition, a deadline, one provision). *agentic* = multi-step (compare, apply to a scenario, calculate, draft).

## Results

Fine-tuned on 2,103 synthetic queries, evaluated on 373 held-out test queries (different source passages from training). Thresholds were tuned on a separate calibration split, never on test.

| | Untrained Laya | Fine-tuned Laya |
|---|---|---|
| Correct route | 55% | **93%** |
| Safety / scope / complexity accuracy | 64% / 50% / 43% | 97% / 97% / 98% |
| Unsafe queries stopped | 87% | 91% |
| Easy queries sent to agentic (wasted cost) | 16% | 1% |
| Hard queries sent to lightweight (quality risk) | 20% | 4% |
| Normal queries wrongly stopped | 64% | 1% |

About 82 ms for all three questions per query on a Kaggle GPU. Tuned thresholds: `unsafe=0.9, out_of_scope=0.6, lightweight=0.5`.

**Read these numbers with care:** queries and labels were written by one LLM (Qwen2.5-7B) and are not hand-verified, so real user messages will score lower. Unsafe recall is the weak spot (98% on calibration, 91% on test); lowering `unsafe` trades more false blocks for fewer misses.

## Use it in code

```python
from orch.backends import LayaBackend      # needs: pip install laya
from orch.router import Orchestrator, Thresholds

backend = LayaBackend("path/to/laya_ft")   # the fine-tuned folder (or the Hub id for untrained Laya)
orch = Orchestrator(backend, Thresholds(unsafe=0.9, out_of_scope=0.6, lightweight=0.5), log_path="decisions.jsonl")
print(orch.run("Quanto tempo ho per denunciare un sinistro RC auto?"))   # Route(route='lightweight', reason='confident_lightweight')
```

Each decision is `{decision, probability, alternatives}`. Each routed query appends one line to `decisions.jsonl` (query, all three decisions, thresholds, route, reason, model name, weights hash). `Orchestrator.run` also emits one MLflow trace per query (spans `safety`, `scope`, `complexity`, `route`).

`DecisionBackend` (`decide(state, question, choices) -> Decision`) is the only thing the router depends on, so another model or the hosted Jev API can replace `LayaBackend` without touching `router.py`.

**Tests** (no GPU, no model download): `pip install pytest mlflow-tracing && pytest -q`

## Web page + MLflow (what runs where)

| What | Where |
|---|---|
| Runs, traces, model registry | Neon Postgres (`MLFLOW_TRACKING_URI`) |
| Weights (~650 MB per version) | Neon Object Storage bucket `mlflow-artifacts` (free plan: 5 GB) |
| Eval runs and weights | experiment `orchestrator-laya` |
| Web-page traces | experiment `orchestrator-app` |
| Registered model | `laya-router`, aliases `champion` (served) and `challenger` |
| Gradio page | `app.py`, runs on your machine |

**Run the page.** Copy `.env.example` to `.env` (git-ignored) and fill it in, then:

```bash
set -a; source .env; set +a
python app.py          # http://127.0.0.1:7860 (7861 if busy); needs: pip install gradio laya torch
```

`app.py` downloads whatever `laya-router@champion` points at (first start: ~650 MB, cached in `models_cache/`) and re-checks the alias every 30 s, so a new champion goes live without a restart. Every query becomes a trace tagged with `registry_version`.

For each query the page shows the route and reason, a table of the three decisions (answer, probabilities, the threshold rule applied, which row decided), the model version and weights hash, the thresholds used, the time taken, a link to the trace in MLflow, the raw decision-log record, and a table of the session's queries. The threshold sliders start at the values tuned with the served model (read from its registered run) and can be changed to see when a route flips.

Optional environment variables: `MLFLOW_UI_URL` (base address of your MLflow UI for the trace link, default `http://127.0.0.1:5001`), `GRADIO_SERVER_NAME=0.0.0.0` (reachable on your network), `GRADIO_SHARE=1` (temporary public gradio.live link; treat it as public).

**Look at it.**

```bash
mlflow ui --backend-store-uri "$MLFLOW_TRACKING_URI" --port 5001    # not 5000: macOS AirPlay uses it
```

- Traces: top-left toggle **GenAI** → Experiments → `orchestrator-app` → Traces. Click a trace, then its `route` span, to see the three probabilities next to the thresholds.
- Registry: top-left toggle **Model training** → **Model registry** → `laya-router` → a version (source, `weights_sha` tag, link to the run with its metrics).

**Do it by hand.**

```bash
python scripts/register_model.py <laya_ft folder> <metrics.json>              # new version, alias `challenger`
python scripts/register_model.py <laya_ft folder> <metrics.json> champion     # ...or straight to champion
```

To promote or roll back: Model registry → `laya-router` → the version → edit **Aliases** → add `champion` (it moves from the old version). The page switches within ~30 s.

## Automated pipeline (GitHub → Kaggle → MLflow → page)

A push to `main` that touches training or evaluation code (the paths are listed in `.github/workflows/pipeline.yml`), or a manual run from the Actions tab:

1. runs the tests;
2. publishes the code to Kaggle and starts the `03-train` notebook (fine-tune + evaluation, 1-2 h);
3. waits for it, downloads the output;
4. skips weights that are already registered (same hash), so a change that does not alter the weights makes no new version;
5. otherwise registers a new `laya-router` version as `challenger`;
6. promotes it to `champion` only if unsafe recall does not drop on test or gold **and** mean routing accuracy is higher (`scripts/ci_register.py`);
7. the running page picks up the new champion on its own.

Limits: training is deterministic, so retraining the same code and data gives the same weights; changing `data/v2` does not retrain (it is a separate Kaggle dataset); the page runs only where you start it (free Hugging Face Spaces no longer host Gradio); Kaggle's weekly GPU quota caps retraining.

### Following a run

Open the run in the repo's **Actions** tab (the `train-and-promote` badge above links to the list). Its **Summary** page has a "Follow this run" box with:

- the Actions run itself (live step log);
- the **Kaggle** notebook, whose page shows the live training log (`https://www.kaggle.com/code/<user>/orchestrator-03-train`);
- the Kaggle code dataset;
- once training is done, an **MLflow** section with the new model version and run as paths to append to your MLflow UI address (for example `http://127.0.0.1:5001/` + `#/models/laya-router/versions/3`). MLflow has no public address here and nothing is logged to it while Kaggle trains, so there is no live MLflow log.

If the Kaggle link shows `***` (Actions masks secrets), add a repo **variable** `KAGGLE_USERNAME` with the same value. The badge shows the last run's result on `main`.

### One-time setup

1. **Neon project** in a region that has Object Storage (`aws-us-east-2`, `aws-us-east-1`, `aws-eu-central-1`, `aws-ap-southeast-1`). Copy its Postgres connection string and write it as `postgresql+psycopg2://…` in `.env` (single-quoted, it contains `&`).
2. **Bucket and keys** (Neon CLI): `neon buckets create mlflow-artifacts`; `neon credentials create --scope storage:read --scope storage:write` (pipeline and `register_model.py`) and `neon credentials create --scope storage:read` (page). Key id → `AWS_ACCESS_KEY_ID` / `AWS_RO_ACCESS_KEY_ID`, `s3_secret_access_key` → the matching secret (shown once). Endpoint and region: `neon api /projects/<project>/branches/<branch>/storage` → `MLFLOW_S3_ENDPOINT_URL`, `AWS_DEFAULT_REGION`.
3. **Experiments with the bucket as artifact location** (it cannot be changed later; `register_model.py` refuses to run otherwise):

   ```bash
   python -c "
   import mlflow
   for n in ('orchestrator-laya', 'orchestrator-app'):
       mlflow.create_experiment(n, artifact_location='s3://mlflow-artifacts/' + n)"
   ```

4. **Kaggle**: the datasets `orchestrator-code` and `orchestrator-data-v2` exist (see below). Create an API token in Kaggle → Settings → API.
5. **GitHub repo secrets** (needs admin on the repo): `KAGGLE_USERNAME`, `KAGGLE_API_TOKEN`, `MLFLOW_TRACKING_URI`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (the **write** pair), `MLFLOW_S3_ENDPOINT_URL` (the literal URL), `AWS_DEFAULT_REGION`.

   ```bash
   for s in KAGGLE_USERNAME KAGGLE_API_TOKEN MLFLOW_TRACKING_URI AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY MLFLOW_S3_ENDPOINT_URL AWS_DEFAULT_REGION; do gh secret set "$s"; done
   ```

6. Merge to `main`. The first registration creates `laya-router` and makes the first version `champion`.

### Troubleshooting

- **Postgres times out** ("connection … port 5432 failed"): the network blocks port 5432 while HTTPS works. Use another network or a VPN.
- **`No module named 'psycopg'`**: use the `postgresql+psycopg2://` scheme (`pip install psycopg2-binary`).
- **`.env:4: parse error near '&'`**: single-quote the Postgres URL in `.env`.
- **`weights would be stored locally`**: the experiment was created without the bucket (usually because `.env` was not loaded in that terminal). Rename it in the UI or the API and recreate it as in setup step 3.
- **Kaggle notebook cannot read Kaggle Secrets** (HTTP 400 for notebooks pushed with the CLI): that is why `03-train` logs to a local SQLite file inside Kaggle and the shared MLflow only gets the result through `register_model.py` / the pipeline.

## Reproduce on Kaggle

Needs the Kaggle CLI (2.x, `pip install kaggle`) with an API token (`export KAGGLE_API_TOKEN=…`) and a phone-verified account. Replace `<user>` with your username.

```bash
KAGGLE_USER=<user> python scripts/make_kaggle.py           # builds dist/
kaggle datasets create -p dist/code -r zip                 # (later: kaggle datasets version -p dist/code -m msg -r zip)

kaggle kernels push -p dist/01-data                        # ~2 h: ~3,000 queries + train/calib/test/gold split
kaggle kernels output <user>/orchestrator-01-data -p kaggle_out3 && cp -r kaggle_out3/out/v2 data/v2
echo '{"title":"orchestrator-data-v2","id":"<user>/orchestrator-data-v2","licenses":[{"name":"other"}]}' > data/v2/dataset-metadata.json
kaggle datasets create -p data/v2

kaggle kernels push -p dist/02-smoke                       # 5-10 min check before the long run
kaggle kernels push -p dist/03-train                       # ~1-2 h: fine-tune + evaluation
kaggle kernels output <user>/orchestrator-03-train -p kaggle_out4
python scripts/register_model.py kaggle_out4/laya_ft kaggle_out4/runs/finetuned/metrics.json   # needs .env loaded
```

Check a run with `kaggle kernels status <user>/orchestrator-<name>`; output can be downloaded only once it is `COMPLETE`. Results land in `kaggle_out4/runs/finetuned/` (`metrics.json`, `cost_vs_accuracy.png`, `decision_log.jsonl`) and `runs/untrained/`. The pipeline does the last three commands for you.

## Layout

```
orch/decision.py     Decision envelope, DecisionBackend interface, the 3 questions
orch/backends.py     LayaBackend
orch/laya_data.py    our labels -> Laya's fine-tuning format
orch/router.py       Thresholds, route(), Orchestrator (decision log + MLflow trace)
orch/evalkit.py      metrics, threshold tuning, sweep, plot
app.py               Gradio page serving laya-router@champion, hot-swaps on alias change
scripts/             build_corpus, gen_queries, split, train_laya, run_eval, make_kaggle,
                     register_model (weights -> registry), ci_register (register + promote rule)
.github/workflows/   tests.yml (unit tests), pipeline.yml (train, register, promote)
.env.example         the variables app.py, register_model.py and the pipeline need
data/v2/             train / calib / test (split by source passage) + gold.csv (50, editable)
tests/               unit tests, run in CI
```

Data sources and licences: [DATA_SOURCES.md](DATA_SOURCES.md). Earlier design notes: `00`–`05_*.md`.
