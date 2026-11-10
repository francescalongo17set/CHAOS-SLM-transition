# Safety check: contract

This document is the agreement between the **Safety check** block and the other blocks of the pipeline (Orchestrator labels, Dispatcher, Answer writer). The executable version of the same agreement is `Contract.py`. Both the stub (`safetyCheck.py`) and the real implementation must follow it.

## Position in the pipeline

```
Broker question -> Safety check -> Orchestrator labels -> Dispatcher -> ...
```

The Safety check replaces the `external, stubbed: pass` block above Orchestrator labels. It is a synchronous filter: it runs before any other block reads the broker's input.

## Scope

The Safety check handles **adversarial security only**: prompt injection (direct and indirect), jailbreak, output hijacking towards the Answer writer, and context manipulation.

It does **not** decide whether the question is in scope, how complex it is, or whether information is missing. Those labels are computed by the trained model in Orchestrator labels.

## Input

| Field | Type | Description |
|---|---|---|
| `broker_question` | `str` | Current question typed or pasted by the broker |
| `artificial_context_window` | `dict` | Context of the conversation (below) |

`artificial_context_window`:

| Field | Type | Description |
|---|---|---|
| `history` | `list[{"role", "content"}]` | Previous turns. `role` is `"user"` or `"assistant"`. Assistant turns contain the plain answer text (the `risposta` field), not the raw JSON of the Answer writer. Ideally read server-side, not sent by the client. |
| `selected_policy` | `str` | ID of the selected policy (must exist in the KB) |
| `library` | `str` | ID of the library (must exist in the KB) |

## Output

The Safety check returns a dict with these keys:

| Field | Type | Description |
|---|---|---|
| `safety_pass` | `bool` | `True` only if the input can proceed |
| `status_code` | `str` | One of the status codes in the table below |
| `threat_type` | `str` | Macro-category of the threat |
| `sub_code` | `str` | Fine-grained code, for internal logs only |
| `risk_score` | `float` | In `[0.0, 1.0]`, compared with `tau_safety` |
| `target_route` | `str \| None` | Route for the Dispatcher |
| `user_message` | `str \| None` | Message to show to the broker, if any |
| `sanitized_input` | `SanitizedInput \| None` | The only text downstream blocks may use |
| `latency_ms` | `float` | Execution time of the check |

`SanitizedInput` is an immutable object with `question`, `history` (a tuple of `(role, content)` pairs), `selected_policy` and `library`.

### Status codes and routes

| `status_code` | `safety_pass` | `threat_type` | `target_route` | Meaning |
|---|---|---|---|---|
| `OK` | `True` | `NONE` | `None` | Input is safe, normal routing |
| `PAYLOAD_TOO_LONG` | `False` | `NONE` | `Ask for clarification` | Operational limit, **not** an attack |
| `SECURITY_BLOCK` | `False` | `STRUCTURAL_OR_CONTEXT_VIOLATION` or `ADVERSARIAL_PROMPT_INJECTION` | `Refuse and re-route` | Attack or invalid context |
| `INTERNAL_ERROR` | `False` | `INTERNAL_ERROR_FAIL_CLOSED` | `Refuse and re-route` | Timeout or model error (fail-closed) |

Route names must match the Dispatcher stubs exactly.

### Example

Safe input:

```json
{
  "safety_pass": true,
  "status_code": "OK",
  "threat_type": "NONE",
  "sub_code": "PASS",
  "risk_score": 0.12,
  "target_route": null,
  "user_message": null,
  "sanitized_input": "<SanitizedInput object>",
  "latency_ms": 18.4
}
```

Blocked input:

```json
{
  "safety_pass": false,
  "status_code": "SECURITY_BLOCK",
  "threat_type": "ADVERSARIAL_PROMPT_INJECTION",
  "sub_code": "SEMANTIC_PROMPT_INJECTION",
  "risk_score": 0.94,
  "target_route": "Refuse and re-route",
  "user_message": "The request cannot be processed because of security checks.",
  "sanitized_input": null,
  "latency_ms": 41.0
}
```

## Rules

1. Downstream blocks use **only** `sanitized_input`. The raw text is discarded. This prevents time-of-check to time-of-use problems.
2. If `safety_pass` is `False`, `sanitized_input` is always `None`.
3. `safety_pass` is `True` if and only if `status_code` is `OK` and `target_route` is `None`.
4. `target_route` must be one of the routes allowed for the `status_code` (table above).
5. **Fail-closed:** if the Safety check result is missing or malformed, the Dispatcher is expected to route to `Refuse and re-route`. This rule is implemented by the Dispatcher, not by the Safety check.
6. `user_message` for `INTERNAL_ERROR` must be neutral ("service temporarily unavailable"): a technical error is not the broker's fault.
7. `sub_code` and the real reason of a block go to the internal logs only, never to the broker.

## The stub

`SafetyCheckStub` has the same interface as the real module, so the rest of the pipeline can be developed and tested before the real Safety check exists.

```python
from safetyCheck import SafetyCheckStub

result = SafetyCheckStub(mode="pass").run(broker_question, artificial_context_window)
sanitized = result["sanitized_input"]   # use only this downstream
```

| Mode | Simulates | Route |
|---|---|---|
| `pass` (default) | Safe input | continues |
| `too_long` | Input too long | `Ask for clarification` |
| `block` | Security block | `Refuse and re-route` |
| `error` | Internal error (fail-closed) | `Refuse and re-route` |

In `pass` mode the stub **inspects nothing and rejects nothing**: every input is accepted, including malformed ones, and the only transformation is NFC normalization. It performs no security check. The other modes return a fixed outcome regardless of the input.

To replace the stub with the real module, keep the same call:

```python
result = run(broker_question, artificial_context_window)
```

## Checking a result

`validate_safety_result(result)` in `Contract.py` returns a list of contract violations (empty list means valid). It is meant for tests of the Safety check; it is not the Dispatcher gate.