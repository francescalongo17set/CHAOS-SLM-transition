# Contributing

## Where your work goes

Find your system in [`docs/pipeline.md`](docs/pipeline.md) and work inside its folder.

## Rules

1. One entry point per system: `run(XIn) -> XOut`.
2. Schemas live only in `contracts/`. Changing one means updating its example in `contracts/examples/` and telling the owners of the systems that use it.
3. Systems never import each other (or `pipeline/`). Only `pipeline/` composes them. A test enforces this.
4. Never commit secrets or model weights.

## Test and run

From the repository root:

```bash
pip install pytest
```

```bash
pytest -q
```

```bash
python -m pipeline.run "your question"
```

`orchestrator/baselines/` and `orchestrator/fine-tuning/` keep their own environments and tests.
