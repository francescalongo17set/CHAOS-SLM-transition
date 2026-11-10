# 01. Data specification and generation

Status: DRAFT v0.1. Read `00_overview_and_rationale.md` first (provenance tags, checkpoint contract, source IDs).

Goal: produce one labelled dataset that every experiment (Kev, Nimble method, S1, S2) can use, plus a frozen hand-written test set.

## 1. Required reading before implementing

- Kev data format and generation docs: `skills/kev-finetune/references/data-format.md` and `data-generation.md` in https://github.com/jaredpalmer/kev `[NOT READ by authors]`.
- Nimble curation guide: `docs/TRAINING_EVAL_CURATION.md` in https://github.com/bespokelabsai/nimble `[NOT READ by authors]`.
- Kev data scripts (standard-library Python, in `skills/kev-finetune/scripts/`): `convert_data.py`, `generate_data.py`, `split_data.py`, `plan_size.py` `[DOC: K-FT]`.

## 2. Canonical record (our format)

`[OUR DECISION]` Store the master dataset as JSONL, one request per line, in this format. All other formats are converted from it.

```json
{
  "id": "req-000123",
  "family": "doc-or-product-family-id",
  "query": "Confronta la polizza X e la polizza Y per il rischio incendio",
  "context": "(no context)",
  "labels": {
    "scope_check": "in_scope",
    "feature_classification": "comparison",
    "complexity_estimation": "complex",
    "slots": {"insurer": "ambiguous", "product": "present", "criteria": "present"}
  },
  "meta": {"cell": "comparison/complex", "generator": "teacher-model-name+version",
           "pair_id": null, "verified": false, "language": "it"}
}
```

Rules:

- `context` is the conversation context (previous turns, selected documents by name or ID, never raw document text). Use the literal string `(no context)` when empty. `[OUR DECISION]` (the Lightweight draft says document references are IDs, not raw text).
- `complexity_estimation` and `slots` exist only when `scope_check` is `in_scope` and the feature is not `none`. `[OUR DECISION]`
- `family` identifies the source document or product family the request was generated from. It is used for splitting (section 6).
- Gold labels must never appear in any model input. `[DOC: N-TRAIN]` ("Each example's gold label stays outside its input prompt.")

## 3. Label spaces

`[OUR DECISION]` (these match `orchestrator_data.py`, our earlier draft)

| Field | Labels |
|---|---|
| `scope_check` | `in_scope`, `out_of_scope`, `quick_reply` |
| `feature_classification` | `regulatory_consultation`, `product_policy_analysis`, `comparison`, `ibip_screening`, `client_drafting`, `none` (`none` = out of scope or quick reply) |
| `complexity_estimation` | `simple`, `complex` |
| slot status (one per required slot) | `present` (stated or resolvable from context), `missing` (not mentioned), `ambiguous` (mentioned but vague or unresolvable, for example "this policy" with none selected) |

Required slots per feature (illustrative; **open point: align with Lightweight 5.1 and Agentic playbooks**):

- regulatory_consultation: topic, date_reference
- product_policy_analysis: insurer, product, coverage_or_topic
- comparison: insurer, product, criteria
- ibip_screening: product, client_profile
- client_drafting: product, client_profile, message_goal

Why a catch-all (`none`, `ambiguous`) exists: a paper found that a model trained with no "none of these" answers avoided them (probability on catch-all options fell from 0.056 to 0.010) and became biased towards "yes". `[DOC: P1 App. G]`

Definition of `complexity_estimation` (needs human agreement before labelling): **simple** = answerable by a lookup of facts or one clause; **complex** = needs multi-step reasoning, trade-offs, comparison across documents, or drafting. `[OUR DECISION]` Label noise is likely here; a later option is to redefine the label as "the lightweight path succeeded" (needs a pipeline run, open point).

## 4. How to generate the data

### 4.1 Principles

1. **Hard labels only.** Both Kev and Nimble train with cross-entropy on the correct answer; neither needs teacher probabilities. `[DOC: K-README "How It Works"; N-README "Finetuning"]`
2. **Labels come from the generation recipe, then are checked.** `[OUR DECISION]` For example, a request generated for the cell "comparison / complex" gets those labels by construction, then a check pass confirms them.
3. **Synthetic labels are not ground truth.** Nimble states its labels are synthetic and model-checked, not human-reviewed, and that separate calls to the same model can make the same mistake. `[DOC: N-README]` So we human-verify a sample (section 5) and hand-write the test set.
4. **Balance and shuffle.** Keep classes balanced per field (cap any class at 2x the rarest) and shuffle option order at training time. `[OUR DECISION, based on P1 §4.3, App. G]`
5. **Include diversity of format and length.** Include short requests and multi-turn contexts; training on only short inputs hurt long-input accuracy in a paper. `[DOC: P1 §4.3]`
6. **Italian first.** Requests are in Italian, with some code-mixed, abbreviated or typo-ridden broker phrasing. None of the repos or papers we read evaluates Italian `[NOT DOCUMENTED]`; Kev's README says fine-tuning helps for "another language" `[DOC: K-README]` but gives no Italian evidence.

### 4.2 Cells and quotas

`[OUR DECISION]` Build a grid and a quota per cell:

- Feature (5) x complexity (2) = 10 in-scope cells, each with a mix of slot patterns (all present, one missing, one ambiguous).
- Out-of-scope requests (other insurance topics, tax or legal advice, other domains) and quick replies (greetings, thanks, "what can you do?").
- Adversarial and hard cases: mixed features in one request, follow-ups that depend on context, injection-like text, negation.

Starting size target: the Kev fine-tune guide says about 1,000 records (for three questions per record) are needed to measure a +5 point gain over the released model, and that with 400 records the gain was inside the noise `[DOC: K-FT]`. Target **1,500 to 3,000 training records**, 300 calibration, 300 test `[OUR DECISION]`. Kev's `plan_size.py` computes the needed size for a given spec `[DOC: K-FT]`.

### 4.3 Generating requests (teacher model)

- Kev's `generate_data.py` generates labelled records from a spec through an "OpenAI-compatible model" and accepts real examples via `--examples` `[DOC: K-FT]`. Whether it can point at a different server (for example a self-hosted open-weights model) is `[NOT DOCUMENTED]`: read the script.
- Which teacher model to use is an open point. Requirements: an open-weights model or one whose terms allow training on its outputs (the team deck flags that some hosted models restrict this). Record the teacher name, version and prompt in `meta.generator`. `[OUR DECISION]`
- Seeds: write 10 to 20 requests per cell by hand (about 100 to 150 in total) as few-shot examples. `[OUR DECISION]`
- **Cache every teacher request and response** to JSONL so generation can be replayed offline and resumed. Nimble does the same: it saves all model requests and responses with the check results so the process can be replayed offline. `[DOC: N-README]`

### 4.4 Contrastive pairs (adapting Nimble's method)

Nimble's method: write two examples that are almost identical and differ in one relevant fact that flips the correct answer; this teaches the model which evidence matters. `[DOC: N-README, "Contrastive data curation"]` Its four steps are `[DOC: N-README]`:

1. Check the decision rules (what facts the rules depend on, and that different answers are possible).
2. Build the pair: change at most eight words in one sentence, changing one "focus fact", so the label changes.
3. Check both examples with separate model calls (facts, policy consistency, no hints of the answer), then remove each evidence sentence in turn and confirm the focus fact becomes unknown.
4. Make labels by code from the checked facts; keep a pair only if every check passes and the two labels differ. Keep both examples of a pair, and all examples of a source family, in the same split.

`[OUR DECISION]` Our mapping (Nimble's method targets context-grounded true/false decisions, not request classification, so this is an adaptation, not a documented use):

- `missing_info`: take a complete request (slot `present`) and edit one phrase so the slot becomes `missing` (for example remove the product name) or `ambiguous` (replace the name with "this policy").
- `complexity_estimation`: change one element that flips simple to complex (for example one product to two products and a comparison criterion).
- `feature_classification`: change the verb or goal so the feature changes while the topic stays.

Pairs are used only for training and calibration; the hand-written test set is independent.

### 4.5 Verification

`[OUR DECISION]`

1. Automated checks on every record: valid JSON, labels in the label space, slots match the feature, no gold label in `query` or `context`, language is Italian, length bounds.
2. A second, independent teacher call per record that answers the labels blind; flag disagreements.
3. Human check of at least 20% of records, oversampling flagged ones and the sensitive features (IBIP, client drafting). Record `verified: true` and the reviewer.
4. De-duplicate within and across splits. Remove any training request that shares a 13-word n-gram with a test request (the contamination filter used in P1 §3.5; our requests are shorter, so also remove near-identical requests by edit distance, threshold to be chosen and logged).

## 5. Splits

`[OUR DECISION]`

| Split | Size | Rule |
|---|---|---|
| train | 1,500 to 3,000 | generated |
| calibration | about 300 | generated or human-written; used only for temperature fitting and threshold selection |
| test | about 300 | **hand-written by a human, frozen**, never used for any tuning decision |

- Split by `family` (document or product family), never by random record, so near-duplicates cannot leak. This follows the project's WP1 protocol and the Nimble practice of keeping source families disjoint between train and holdout. `[DOC: N-DATASET]`
- Kev advises keeping 10 to 20% of the file aside for evaluation `[DOC: K-README, "By Hand"]`; our test and calibration sets are separate from that.
- Do not tune hyperparameters or choose checkpoints on the test set; Nimble gives the same rule for its holdout. `[DOC: N-TRAIN]`
- Thresholds need enough positives: a paper found that a 5% miss target needed several hundred positives in the calibration data, or a conservative margin. `[DOC: P3 §6]` Check that the calibration split has enough examples of the sensitive features and report counts.

## 6. Conversion to each tool's format

### 6.1 Kev (documented format)

Kev's training file is JSONL, one request per line, in the same shape as an API request plus a `label` on every question. `[DOC: K-README, "By Hand"]` For a `choice` the label is the option name; for a `noul` it is `true` or `false`; for a `score` it is the level's position starting at 0. The question id is chosen by us and the model never sees it. `[DOC: K-README, API]` Options are given as `criteria` (option name to description, or `null`). `[DOC: K-README, API]`

Documented example shape:

```json
{"state": {"subject": "Charged twice", "body": "I see two charges for order #4411. Please refund one."},
 "questions": {
   "team": {"type": "choice", "instructions": "Which team should handle this ticket?",
            "criteria": {"billing": "Payments and refunds", "shipping": "Delivery problems"}, "label": "billing"}}}
```

`[OUR DECISION]` Our mapping (two-stage, because the slot questions depend on the feature):

- **Stage A record:** `state` = object with `context` and `query`; questions `scope` (choice, 3 options), `feature` (choice, 6 options), `complexity` (choice, 2 options; omit the question for out-of-scope or quick-reply requests).
- **Stage B record:** same `state`; one `choice` question per required slot of the gold feature, with the slot name inside `instructions` (because the id is not seen by the model), options `present` / `missing` / `ambiguous` with descriptions.

Whether Kev's trainer accepts records with different question sets `[NOT DOCUMENTED]`. Validate with Kev's `split_data.py` (it validates records) and a short training smoke test; if rejected, report the exact error and fall back to one question set per record by adding the `none`/not-applicable option to `complexity`. Option names must be exact strings; descriptions should be written in the same language as the query unless a test shows otherwise `[NOT DOCUMENTED]`.

### 6.2 Nimble

`[NOT DOCUMENTED]`: the field layout of Nimble's `data/train.jsonl` was not read. Nimble's loader also requires a `data/manifest.json` and verifies evidence certificates, blind reviews, file hashes and disjoint source families. `[DOC: N-TRAIN, N-DATASET]` Using our data with Nimble's trainer therefore needs the exact schema from the code. See `03_exp_nimble.md`.

### 6.3 S1 and S2 (our baselines)

Generated from the canonical record by the functions in `orchestrator_data.py` (our earlier draft, not run against a real model). See `04_exp_own_baselines.md`.

## 7. Known issues in Kev's data scripts

- `split_data.py`, `convert_data.py` and `generate_data.py` read files with `str.splitlines()`, which also splits lines at the characters U+2028, U+2029 and U+0085. A record containing them can be dropped by `split_data.py` (which still exits with 0) or crash the other two scripts. `[DOC: K-ISSUE276, search snippet; check whether it is fixed]` Mitigation: strip those characters from all text before writing JSONL and check that the number of valid records after splitting equals the number written. `[OUR REQUIREMENT]`

## 8. Checkpointing for data generation (hardware contract applies)

`[OUR REQUIREMENT]`

- Generation is a long, interruptible job. Append each finished record immediately to a JSONL file on persistent storage; never keep results only in memory.
- Give every request a stable ID derived from (cell, seed index); on restart, skip IDs that already exist.
- Cache all teacher responses (section 4.3) so a restart never repeats paid or slow calls.
- Write `STATE.json` with counts per cell, so quotas are resumable.
- Run the verification and split steps as separate resumable stages with their own output files.

## 9. Outputs of this stage

- `data/master.jsonl` (all records), `data/train.jsonl`, `data/calibration.jsonl`, `data/test_handwritten.jsonl`.
- `data/manifest.json`: file hashes (SHA-256), counts per field, class balance, teacher model and prompts, seeds. Both Kev and Nimble record hashes so results can be traced to exact data. `[DOC: K-README, N-DATASET]`
- A short data card: label definitions, known label-noise risks, share verified by humans.

## 10. Open points

1. Final slot lists (align with Lightweight and Agentic designs).
2. Which teacher model (licence for training on outputs).
3. Agreement on the definition of `complex`.
4. Whether the model input is pseudonymised text.
5. Whether Kev's trainer accepts variable question sets per record.
