# Stage 1: Extract (code/extract.py)

- PyMuPDF, 1-based pages, reading order by block position; two-column detection from narrow blocks on both sides; tables from `find_tables()` rebuilt from the text lines in each cell (cells joined with " | ").
- Page counts 53 / 140 / 188 match section 3. Output: extracted/<doc_id>.jsonl, page_report.csv, toc_<doc_id>.json (only Generali has an outline: 255 entries).
- Low-text pages (<200 chars): Generali only, pages 2 (blank page), 40, 117 = 3 of 140 (2.1%, under the 5% stop limit). Salute and Impresa: none. No OCR.
- Two-column pages: Salute 2; Generali 3, 4, 70, 71, 100, 109; Impresa 2, 53, 99, 100, 112, 179.
- Header/footer removal: lines in the top/bottom 8% repeating on at least 30% of pages **or on at least 10 pages**, plus page-number lines. The 10-page rule is a deviation: the Impresa sub-documents (52-page DPA footer, 27% of pages) would otherwise survive.
- Known limitations: (1) unruled tables (for example Generali p109) are read column by column, so row pairing is lost; (2) some DIP layouts split a sentence across blocks (Salute p2). Both affect a few pages per document.
