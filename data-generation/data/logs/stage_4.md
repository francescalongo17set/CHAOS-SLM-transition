# Stage 4: Index and retrieval (code/embed.py, code/retrieve.py)

- Embedded all 1,019 chunks with both candidates on Apple MPS: multilingual-e5-base (768 dim, prefix "passage: ", max 512 tokens, 131 s) and bge-m3 (1024 dim, no prefix, max 1024 tokens, 356 s). Vectors are L2-normalised, saved in index/emb_*.npy in the row order of chunks.jsonl (index/chunk_order.json).
- retrieve(question, doc_id, k=5, model=None): exact dot product, doc_id filter, ties broken by chunk order, scores rounded to 4 decimals. Returns {rank, score, chunk_id, doc_id, page, section_path, text}.
- index/retrieval_config.json lists both candidates with pinned revisions; "active" is a placeholder (e5). The choice is frozen at stage 6 on hit@5.
- Acceptance: the same top 5 on a repeated query (3 queries x 2 models) and the doc_id filter honoured: pass.
- Note: e5-base truncates at 512 tokens, so the tail of the longest chunks (about 1,900+ characters) is not embedded. bge-m3 uses 1,024 tokens. Compare both at the pilot.
