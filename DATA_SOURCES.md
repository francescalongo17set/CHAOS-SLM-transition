# DATA_SOURCES

Checked on 2026-11-09 against the Hugging Face repos themselves (metadata, README, and the actual files). Not legal advice.

## Used

| Source | Licence (as stated) | What we use it for | Verified |
|---|---|---|---|
| [`diatribe00/normattiva-lab-data`](https://huggingface.co/datasets/diatribe00/normattiva-lab-data) (OpenNormattiva VOOM mirror, built 2026-05-10) | **Conflict:** HF metadata says `mit`; the README says the data comes from Normattiva Open Data under **IODL 2.0**. We treat the legal texts as IODL 2.0 (the stricter one: keep attribution and the source) and the repo's own packaging as MIT. | Source passages for in-scope queries | see below |
| [`AndreaSimeri/Italian_Civil_Code`](https://huggingface.co/datasets/AndreaSimeri/Italian_Civil_Code) | Apache-2.0 (HF metadata) | Codice civile arts. 1882-1932 (the insurance title) | 51 articles present, text is lower-cased |
| [`itacasehold/itacasehold`](https://huggingface.co/datasets/itacasehold/itacasehold) | Apache-2.0 (HF metadata) | Seeds for "legal but not insurance" out-of-scope queries (administrative-law holdings, `summary` field, train split, 792 rows) | present |
| Qwen2.5-7B-Instruct | Apache-2.0 | writes the synthetic queries (generator only, not a decision model) | licence from HF metadata |
| [`convaiinnovations/laya-multilingual`](https://huggingface.co/convaiinnovations/laya-multilingual) | Apache-2.0 | **the decision model**, fine-tuned on our labels. PyPI package `laya` (Apache-2.0), used on Kaggle only | licence from HF metadata and PyPI; code partly read, not audited |

**Not used on purpose:** IVASS documents (reuse licence unclear). **Qwen2.5-3B-Instruct** is not used: its licence is the non-Apache Qwen research licence, not free for every use.

Attribution line to keep with any published result: *"Contains Italian legislation from Normattiva (IODL 2.0) via diatribe00/normattiva-lab-data; Italian Civil Code via AndreaSimeri/Italian_Civil_Code (Apache-2.0); ITA-CaseHold (Apache-2.0)."*

## What is actually in the Normattiva mirror (insurance check)

Result: yes. Found in `data/processed/laws_vigente.jsonl` (full text) and, for the Codice, also as XML in `data/raw/Codici_vigente.zip`.

- **D.Lgs. 209/2005, Codice delle assicurazioni private** (`urn:nir:stato:decreto.legislativo:2005-09-07;209`), consolidated version valid 2026-04-07, 555 articles of at least 300 characters. It contains the RC auto rules (compulsory insurance, direct compensation).
- RC auto around it: D.P.R. 254/2006 (risarcimento diretto), D.P.R. 973/1970 (regulation of L. 990/1969), D.Lgs. 198/2007 (directive 2005/14/CE), L. 39/1977 (conversion of the 1976 RC auto decree).
- Distribution and supervision: D.Lgs. 68/2018 (IDD) and its 2020 correction (D.Lgs. 187/2020), D.Lgs. 74/2015 (Solvency II), D.Lgs. 224/2016 (PRIIPs documents), D.Lgs. 174 and 175/1995 (life and non-life), D.Lgs. 182/2006 (notary liability insurance).
- **Not in the in-force track:** L. 990/1969 itself (RC auto original). It is repealed and its rules moved into the Codice, so it sits in the repealed (`abrogati`) track which we do not use.

`scripts/build_corpus.py` re-checks all of this on every run and writes `corpus_check.json`; the list of extra laws is a fixed list of URNs (a title search also matches accounting directives).

## Derived data

`data/v2/{train,calib,test}.jsonl` and `gold.csv` (a subset of test) are synthetic queries written by Qwen2.5-7B-Instruct from the passages above. They contain queries and labels plus a source reference, not the passages. Generator name and Hub revision are stored per row and in `gen_report.json`.

## Considered and not used

Jev (TypeSafe): closed, paid API, no confirmed free tier. Von: Apache-2.0 but English-only and archived. Kev: Apache-2.0, a Qwen LLM with a decision head. jevlike: a trainer with no pretrained model. NanoJev: built for game tasks. Public prompt-injection sets (deepset/prompt-injections Apache-2.0, Lakera/gandalf_ignore_instructions MIT) are English-only and optional for a later round.
