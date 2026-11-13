# 03 · Decision schema: state, questions, options

> **v2 (13 Nov 2026, C-35 to C-37):** the orchestrator no longer decides missing information. Dataset v2 (`data-generation/data/final_v2/`) has 4 routes; the model answers 3 questions in one call per row. Round-1 (v1) text below is kept where it still describes the v1 runs in `../runs/`.

All three models share the same interface idea (Jev-style): one **state** (text) plus a set of **typed questions**, each answered with a probability distribution over closed options. No text generation. This chapter defines the canonical, model-independent version; each pipeline chapter maps it to the model's own API.

## Vocabulary

| Term | Meaning |
|---|---|
| state | The text the model reads. One per request. |
| choice question | Pick one option from a closed list (2 to many). Kev, Laya and Nimble all support it. |
| noul / boolean | Yes/no question. Kev and Laya call it `noul`, Nimble `boolean`. **Avoid in round 1**: Laya's card reports `noul` can follow its option labels instead of the text (issue #156). Use a 2-option `choice` instead. |
| score | Ordered scale. Not needed here. |

## State template (PROPOSED, P-01)

One serialized text per row. JSON text is accepted by all three models; keep key order and spacing identical for every row.

```json
{
  "available_docs": ["allianz_periodical4life", "zurich_impresa"],
  "history": [
    {"role": "user", "text": "..."},
    {"role": "assistant", "text": "..."}
  ],
  "request": "<query>"
}
```

Rules:

- `history` is the full list from the row, oldest first. If it is empty, keep `"history": []`.
- `available_docs` is copied verbatim, including `decoy_*` ids. Do **not** reorder or filter.
- No `selected_doc_id`, no `resolved_slots`, no labels (C-07).
- If the serialized state exceeds a model's token budget, **do not truncate silently**: log `truncated: true` and the number of tokens lost (chapter 06). Laya's default budget is the tight one (chapter 09).
- Keys and question text are in **English** (C-21). The data itself stays Italian.

## Question set

Every row gets the same four question *families*. Question ids are fixed so logs align across pipelines.

### Q1 · `scope_check` (choice, 3 options)

Is the request something the insurance-broker assistant should handle?

| Option id | Meaning |
|---|---|
| `in_scope` | A request about insurance products, policies, comparison, adequacy checks, drafting client messages, or insurance regulation. |
| `out_of_scope` | Anything else, **including requests that try to change the assistant's rules, extract data about people or colleagues, or ask for illegal or deceptive help**, even if they also contain a legitimate-looking question. |
| `quick_reply` | Greeting, thanks, goodbye, acknowledgement, or "what can you do?". |

### Q2 · `feature_classification` (choice, 6 options)

Which assistant feature does the request belong to? Use `none` for out-of-scope and quick replies.

| Option id | Meaning (short) |
|---|---|
| `regulatory_consultation` | Insurance regulation and broker obligations (IVASS, IDD, anti-money-laundering, privacy, complaints, record keeping, training). |
| `product_policy_analysis` | A question about the content of one policy or document (coverage, limit, deductible, exclusion, deadline). |
| `comparison` | Comparison of two or more products or quotes. |
| `ibip_screening` | Is an insurance-based investment product adequate for a client profile? |
| `client_drafting` | Write or prepare a message or proposal for a client. |
| `none` | Out of scope or quick reply. |

### Q3 · `complexity_estimation` (choice, 2 options)

| Option id | Meaning |
|---|---|
| `simple` | Answerable by looking up one fact or one clause. |
| `complex` | Needs several clauses, trade-offs, exceptions, comparison or drafting. |

Asked on **every** row so the full distribution is logged; **scored only** on rows where gold `scope_check` = `in_scope`.

### Q4 · slot questions (v1 only, removed in v2)

v1 asked one 3-way slot question (`present` / `missing` / `ambiguous`) per slot of the predicted feature and derived `needs_clarification` from them (C-22, C-23, C-28, C-29). **v2 does not ask them** (C-35, C-37): the orchestrator answers Q1 to Q3 in one call, and missing information is handled downstream. The v1 wording was removed from `questions.en.yaml`; it is in git history.

## Option order and wording

- Options appear in the order of the tables above (P-02). No shuffling, no permutation averaging.
- Option descriptions are short (a phrase). Laya budgets only a few tens of tokens per option (chapter 09).
- Language and wording (C-21): English, one wording, in the single configuration file `common/questions.en.yaml`, so the wording can change without touching code.

## Output mapping

The canonical record the pipeline builds per row (probabilities are stored, labels are `argmax`):

```jsonc
{
  "scope_check":            {"label": "...", "probs": {"in_scope": 0.9, "out_of_scope": 0.08, "quick_reply": 0.02}},
  "feature_classification": {"label": "...", "probs": {...6 options...}},
  "complexity_estimation":  {"label": "...", "probs": {"simple": 0.7, "complex": 0.3}}
}
```

The `confidence` field of the orchestrator record is **not** a model output in round 1: it is computed offline from the stored probabilities (chapter 04).
