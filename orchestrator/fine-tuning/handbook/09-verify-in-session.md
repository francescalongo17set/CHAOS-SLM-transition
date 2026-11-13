# 09 · Verify in session

None of the upstream facts in chapters 05 and 06 has been run. The owner decided to trust them as written (FT-C-05), but each item below must be **checked in the session before it is relied on**. A failed check stops the work and goes to the owner (`BLOCKED: ...`). Record every answer in `run.json` notes or `train_report.json`.

## Kev

1. At the pinned sha of `kev`:
   - Does `--data` pass records through `augment` (it "always shuffles option order" for choice questions)?
   - What does `--init_from` expect for a Hub repo (revision syntax `@rev`)?
   - What are the exact `meta.extra["args"]` keys and contents of the released checkpoint (0.8B first, then 4B)?
2. Does `kev.train` run on a T4: 0.8B with fp32, later 4B with `--dtype bf16 --weights_dtype bf16` (emulated bf16)? Measure real step time and memory for each (pilot C2). **The 0.8B answer comes first and settles items 1 and 3 for both sizes.**
3. What are `MAX_STATE` and the packed limits as seen by `kev.model.fits` on our longest records with 7 questions? Zero drops are allowed.

## Laya

4. In `laya.train` (version 0.4.31):
   - `read_data` accepts our JSONL with `expected`.
   - Slot question ids that contain `:` are accepted.
   - `laya.load(<local dir>)` works on a saved checkpoint.
   - The signatures of `train_model` and `on_epoch_end`.
   - The multilingual config's `max_len` and `head_max_len` (expected 1024 and 256).

## Both

5. Things the upstream docs read for the spec did **not** show: Kev's learning-rate and epoch choices for the released 4B (taken from the checkpoint meta at run time), the full CLI list of Laya (no argparse was found), Laya's `collate_items` signature.
6. Kaggle free-tier GPU session length and weekly quota, per account. Re-check; the figures change. Note the values in the run notes.
8. Kev only (FT-C-25): the prebuilt `causal_conv1d` wheel installs in the Kaggle venv and passes the notebook's GPU check (`causal_conv1d kernel OK`, T4 sm_75). Not yet run anywhere. Record the printed wheel sha256 and whether the kernel or the fallback was active in the run notes; if the check fails the run continues on the fallback and must say so.
7. Whether the runners can produce both raw and calibrated probabilities for the ECE pair (FT-C-15), and how.

## What to do on failure

Do not work around it. Write `BLOCKED: <which item>, <what you observed>, <options you see>`, stop that branch, and leave the other branches running (they are independent, FT-C-03).
