You are a data writer. Work from `/Users/antonioponti/Desktop/Data Science/CHAOS-SLM-transition/data-generation/data` (cd there). Python: `/Users/antonioponti/miniconda3/envs/navisio/bin/python -I`.
Read ONLY `writer_card.md`. Do not read any other file (not validate.py: the card and the job print give every shape you need), do not explore, do not re-read your outputs.
WRITE EVERY RECORD YOURSELF, one by one, as natural varied Italian. NEVER generate records with a script, loop, template or string substitution: batches produced that way are discarded and rewritten. Each query must differ in structure and wording from the others in your list.
Your jobs: the ids in `<LIST>`. Work in groups of at most 10 records:
1. Print the jobs: `python -I code/show_job.py --file <LIST>` is too big for one go, so print a few jobs at a time with `python -I code/show_job.py job-A job-B job-C` (use `code/brief.py` for no-document jobs).
2. Write the written fields per the card as a JSONL batch file `staging/bulk/<NAME>/b<NN>.jsonl` (one line per record, with job_id). Write whole bundles together.
3. ONE command validates, runs the retrieval check and stages: `python -I code/write_batch.py staging/bulk/<NAME>/b<NN>.jsonl --dir staging/bulk/<NAME> --writer <your exact model id from your system prompt>`. Do not run any other check.
4. Fix REJECT lines and resubmit the whole job (bundles) or only the bad record; at most 3 tries per job, then submit a skip line per the card. If the retrieval server is not running, stop and report.
Final report, at most 5 lines: jobs done, skipped job ids with reason, number of first-attempt rejects. No per-record echo, no summaries of content.
