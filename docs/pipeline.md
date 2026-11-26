# Pipeline

```
question + context window
  -> safety ── blocked ──> refusal message
  -> orchestrator (decision model + dispatcher)
  -> quick_reply | refuse | lightweight | agentic
  -> verification
  -> answer + sources
```

Every system exposes `run(XIn) -> XOut`. Types are in [`contracts/`](../contracts/), one example per system in [`contracts/examples/`](../contracts/examples/).

| System | Folder | Entry point | In | Out | Today |
|---|---|---|---|---|---|
| Safety check | `safety/` | `safety.run.run` | question, context | pass/block, sanitized question and context | stub: passes everything |
| Decision model + dispatcher | `orchestrator/` | `orch.run.run` | question, context, tau | route, reason, confidence | stub: always `agentic` |
| Quick reply | `quick_reply/` | `quick_reply.run.run` | question, context | answer | stub |
| Lightweight (RAG + answer writer) | `lightweight/` | `lightweight.src.run.run` | question, context | answer + sources | stub |
| Agentic | `agentic/` | `agentic.run.run` | question, context | answer + sources | stub |
| Verification | `verification/` | `verification.run.run` | question, route, answer | passed, answer | stub: passes everything |

`refuse` has no system: `pipeline/run.py` returns a fixed message, which still goes through verification. A safety block returns directly.

## Open items

- **No real safety filter or answer checking.** Both are stubs; do not expose this to users.
- **Confidence override (tau).** Pending owner decision X-04. The field is in the contract and nothing reads it. The v2 rule table without tau is in `orchestrator/baselines/common/dispatcher.py`.
- **Code on other branches, not ported:** `orchestrator-jev` (`orch/`, `app.py`, training scripts, workflows) and `safety-check` (`safetycheck/`). Their output shapes differ from `contracts/`, so porting needs a small adapter in each `run.py`.
