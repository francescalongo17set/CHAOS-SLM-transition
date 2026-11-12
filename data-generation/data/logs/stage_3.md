# Stage 3: Catalogue (code/catalogue.py)

- field_lexicon.yaml: the 11 fields of the book plus 8 extensions (pagamento del premio, validità territoriale, prescrizione, surrogazione, dichiarazioni e aggravamento, tutela legale, diaria, legge applicabile e foro) and extra terms (for example "termine di aspettativa" for carenza).
- chunk_catalogue.jsonl: coverage, fields_found, has_value, has_condition, is_list, usable_for for all 1,019 chunks.
- **Deviation:** single_value is now "has_value" instead of "has_value and exactly one field". With the shared lexicon only 9 Salute train chunks passed the strict test against a quota of 128.
- absent_candidates.csv: zero-hit topics are usable (confirmed = false). Topics whose expected section is the held-out Assistance section are assigned to validation, all others to train; Impresa topics to test.
- comparable_fields.csv: 14 fields in train, 5 in validation, 14 in test.
- catalogue_summary.md holds the capacity-versus-demand tables.
