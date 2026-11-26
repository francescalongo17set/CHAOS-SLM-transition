# Who works where

Find your part below. It tells you which folder is yours, what you receive and what you must give back.

> Today every part is a placeholder: nothing is filtered, answered or checked for real yet.

## How a question travels

1. A broker asks a question. We attach the **context**: the earlier messages, the selected policy and the library.
2. **Safety** decides whether the question may continue. If not, the broker gets a refusal and it stops here.
3. The **orchestrator** picks a path. Inside it:
   - the **decision model** reads the question and says how confident it is;
   - the **dispatcher** then applies its rules to that, including the confidence threshold (**tau**), and chooses the path.
4. One path runs: **quick reply**, **refuse**, **lightweight** or **agentic**.
5. **Verification** checks the answer.
6. The broker gets the answer and its sources.

## The same for everyone

- Your code goes in your folder. You fill in one function, `run`, in the file named below.
- Your input and output are fixed. They are written in `contracts/`, with a filled-in example in `contracts/examples/`.
- Do not use code from another person's folder.
- If you need a different input or output, talk to the team first, because others depend on it.
- To check you broke nothing, type `pytest -q` in the main folder of the project.

---

## Safety

**Your job:** stop questions that should not be processed.

- **Your file:** `safety/run.py` (hiding personal data goes in `safety/anonymize.py`)
- **You receive:** the question and the context
- **You give back:**
  - may it continue: yes or no
  - a short status code (`OK` when it may continue)
  - if yes: a cleaned copy of the question and context, which is all the later parts see
  - if no: a message for the broker
- **Contract and example:** `contracts/safety.py`, `contracts/examples/safety.json`

## Orchestrator (decision model and dispatcher)

**Your job:** choose the path. You do not write the answer.

- **Your file:** `orchestrator/src/orch/run.py`
- **You receive:** the question, the context and, optionally, tau
- **You give back:**
  - the path: `quick_reply`, `refuse`, `lightweight` or `agentic`
  - the reason for the choice
  - the confidence, from 0 to 1
- **Contract and example:** `contracts/orchestrator.py`, `contracts/examples/orchestrator.json`
- **Also yours:** `orchestrator/baselines/` and `orchestrator/fine-tuning/` (model experiments)

For example, "How much notice is needed for direct payment?" is a single lookup, so the answer could be: path `lightweight`, confidence `0.91`.

## Quick reply

**Your job:** answer greetings, thanks and "what can you do?".

- **Your file:** `quick_reply/run.py`
- **You receive:** the question and the context
- **You give back:** the answer
- **Contract and example:** `contracts/quick_reply.py`, `contracts/examples/quick_reply.json`

## Lightweight

**Your job:** find the right passages in the documents (RAG) and write an answer from them.

- **Your file:** `lightweight/src/run.py`
- **You receive:** the question and the context
- **You give back:** the answer and the passages it is based on
- **Contract and example:** `contracts/lightweight.py`, `contracts/examples/lightweight.json`
- **Also yours:** the rest of `lightweight/` (notebooks and experiments)

## Agentic

**Your job:** answer questions that need several steps, such as comparing two policies.

- **Your file:** `agentic/run.py`
- **You receive:** the question and the context
- **You give back:** the answer and its sources
- **Contract and example:** `contracts/agentic.py`, `contracts/examples/agentic.json`

## Verification

**Your job:** check the answer before the broker sees it.

- **Your file:** `verification/run.py`
- **You receive:** the question, the path that was taken, and the answer with its sources
- **You give back:** passed or not, and the answer to show. If it did not pass, give a safe replacement answer.
- **Contract and example:** `contracts/verification.py`, `contracts/examples/verification.json`

## Refuse

Nobody owns this one. It is a fixed message in `pipeline/run.py`.

## Connecting the parts

Only `pipeline/` connects the parts, in the order above. You normally do not need to touch it.
