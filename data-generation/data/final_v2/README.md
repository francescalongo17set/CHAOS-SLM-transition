# Dataset v2 (derived from final/)

Same rows and text as v1. Only `support.expected_route` changed: the `clarification` route is gone (the agent gathers missing information itself).

- v2 rule: out_of_scope -> refuse; quick_reply -> quick_reply; IBIP, client drafting or complex -> agentic; otherwise lightweight.
- The 508 v1 clarification rows move to `agentic` (414, sensitive or complex) or `lightweight` (94, simple and not sensitive).
- `labels.missing_info`, `support.slot_status`, `required_slots`, `filled_slots` and `support.expected_route_v1` are kept as metadata. They are not scored and not used for training in v2.
- Rebuild with `python -I code/make_v2.py`.
