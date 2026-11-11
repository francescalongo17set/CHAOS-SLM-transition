# Stage 0: Setup (2026-11-10)

- Layout created under `data-generation/data/` (raw/ holds the PDFs; extracted, chunks, catalogue, index, seeds, plan, cache, staging, verify, review, final/{train,validation,test_package}, code, logs).
- Conda env `navisio`, Python 3.11.18. Packages: PyMuPDF 2.1, sentence-transformers 6.2.0, torch 2.15.0, numpy, PyYAML, RapidFuzz, lingua. Pinned in code/requirements.txt.
- PDF page counts (PyMuPDF): Zurich Salute 53, Generali Immagina Adesso 140, Zurich Impresa 188 -> match section 3. Allianz 97 pp, Italiana R&I+ 82 pp (name only, never extracted).
- PDF outline: only Generali has one (255 entries); the Zurich documents need font-based headings (as the book says).
- Both embedding models reachable on Hugging Face; config.json downloaded for each. Full weights are downloaded at stage 4.
- Writer/blind checker model id: claude-sonnet-5-5 (from the session). Seed 20261110. Details in env.json.
- Open: fresh-context sub-agents not yet exercised (done at stage 6).
- Result: acceptance check passed.
