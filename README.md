# Insurance-law orchestrator

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

## Use it

```python
from orch.backends import LayaBackend      # needs: pip install laya
from orch.router import Orchestrator, Thresholds

backend = LayaBackend("path/to/laya_ft")   # the fine-tuned folder (or the Hub id for untrained Laya)
orch = Orchestrator(backend, Thresholds(unsafe=0.9, out_of_scope=0.6, lightweight=0.5), log_path="decisions.jsonl")
print(orch.run("Quanto tempo ho per denunciare un sinistro RC auto?"))   # Route(route='lightweight', reason='confident_lightweight')
```

Each decision is `{decision, probability, alternatives}`. Each routed query appends one line to `decisions.jsonl` (query, all three decisions, thresholds, route, reason, model name, weights hash). The fine-tuned weights (~650 MB) are not in git: they are in the output of the `03-train` Kaggle notebook.

`DecisionBackend` (`decide(state, question, choices) -> Decision`) is the only thing the router depends on, so another model or the hosted Jev API can replace `LayaBackend` without touching `router.py`.

**Tests** (no GPU, no model download): `pip install pytest mlflow-tracing && pytest -q`

**MLflow:** runs (params, metrics, charts) are in a local SQLite file; open them with `mlflow ui --backend-store-uri sqlite:///mlflow.db`. `Orchestrator.run` also emits one MLflow trace per query (spans: `safety`, `scope`, `complexity`, `route`); `run_eval.py` does not.

## Reproduce on Kaggle

Needs the Kaggle CLI with an API token and a phone-verified account. Replace `<user>` with your username.

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
```

Check a run with `kaggle kernels status <user>/orchestrator-<name>`; output can be downloaded only once it is `COMPLETE`. Results land in `kaggle_out4/runs/finetuned/` (`metrics.json`, `cost_vs_accuracy.png`, `decision_log.jsonl`) and `runs/untrained/`.

## Automated pipeline (GitHub → Kaggle → MLflow → Gradio)

Pushing a change to `main` that touches training or evaluation code (paths listed in `.github/workflows/pipeline.yml`) runs the tests, retrains on Kaggle, registers the weights as `laya-router` in MLflow, and moves the `champion` alias if the new model is better (no drop in unsafe recall on test or gold, higher mean routing accuracy; see `scripts/ci_register.py`). Weights already registered (same hash) are skipped, so a change that does not alter the weights does not create a version. `app.py` checks the alias every 30 s and swaps models without a restart. Takes 1-2 h end to end, dominated by Kaggle.

MLflow state: Neon Postgres (runs, traces, registry) + Neon Object Storage bucket `mlflow-artifacts` (weights). Credentials never go in git; copy `.env.example` to `.env` locally and add the same values as repo secrets for the workflow:

```bash
for s in KAGGLE_USERNAME KAGGLE_KEY MLFLOW_TRACKING_URI AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY MLFLOW_S3_ENDPOINT_URL AWS_DEFAULT_REGION; do gh secret set $s; done
set -a; source .env; set +a; python app.py                 # local UI at http://127.0.0.1:7860 (7861 if busy)
python scripts/register_model.py <laya_ft> <metrics.json>  # by hand: registers as `challenger`
```

In the MLflow UI switch to **Model training** (top left) to see the **Model registry**; traces are under **GenAI** → Experiments → `orchestrator-app`.

## Layout

```
orch/decision.py   Decision envelope, DecisionBackend interface, the 3 questions
orch/backends.py   LayaBackend
orch/laya_data.py  our labels -> Laya's fine-tuning format
orch/router.py     Thresholds, route(), Orchestrator (decision log + MLflow trace)
orch/evalkit.py    metrics, threshold tuning, sweep, plot
scripts/           build_corpus, gen_queries, split, train_laya, run_eval, make_kaggle
data/v2/           train / calib / test (split by source passage) + gold.csv (50, editable)
tests/             unit tests, run in CI
```

Data sources and licences: [DATA_SOURCES.md](DATA_SOURCES.md). Earlier design notes: `00`–`05_*.md`.
