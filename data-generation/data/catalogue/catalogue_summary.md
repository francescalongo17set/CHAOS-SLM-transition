# Catalogue summary (stage 3)

## Usable chunks per document, pool and question type

| doc | pool | chunks | single_value | conditional | multi_fact | list/table chunks |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| zurich_salute | train_pool | 132 | 59 | 43 | 114 | 63 / 5 |
| zurich_salute | validation_pool | 32 | 13 | 13 | 25 | 20 / 0 |
| generali_immagina_adesso | train_pool | 267 | 145 | 115 | 192 | 89 / 46 |
| generali_immagina_adesso | validation_pool | 52 | 42 | 6 | 24 | 16 / 3 |
| zurich_impresa | test_pool | 536 | 165 | 123 | 405 | 257 / 114 |

## Capacity of value-bearing chunks vs demand (single_value + conditional)

| doc | pool | value chunks | demand | base cap | capacity at base | share of capacity | ladder step needed |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| zurich_salute | train_pool | 59 | 208 | 3 | 177 | 118% | 2: cap 4 |
| generali_immagina_adesso | train_pool | 145 | 344 | 3 | 435 | 79% | 1: 100% at base cap |
| zurich_salute | validation_pool | 13 | 49 | 3 | 39 | 126% | 2: cap 4 |
| generali_immagina_adesso | validation_pool | 42 | 49 | 3 | 126 | 39% | none (70% rule) |
| zurich_impresa | test_pool | 165 | 325 | 2 | 330 | 98% | 1: 100% at base cap |

## Absent topics (zero hits, usable)

| doc | split | usable topics | max absent questions (5 per topic) | planned absent quota |
| --- | --- | ---: | ---: | ---: |
| zurich_salute | train | 25 | 125 | 64 |
| generali_immagina_adesso | train | 27 | 135 | 106 |
| zurich_salute | validation | 11 | 55 | 15 |
| generali_immagina_adesso | validation | 10 | 50 | 15 |
| zurich_impresa | test | 21 | 105 | 100 |

## Comparable fields (fields found on both sides)

| split | fields | thresholds (8/4/8) |
| --- | ---: | --- |
| train | 14: franchigia, massimale, carenza, esclusioni, rimborso, decorrenza, durata, recesso e disdetta, denuncia del sinistro, assistenza, pagamento del premio, validità territoriale, surrogazione, tutela legale | OK |
| validation | 5: massimale, esclusioni, rimborso, assistenza, validità territoriale | OK |
| test | 14: franchigia, massimale, carenza, esclusioni, rimborso, decorrenza, durata, recesso e disdetta, denuncia del sinistro, assistenza, pagamento del premio, validità territoriale, surrogazione, tutela legale | OK |