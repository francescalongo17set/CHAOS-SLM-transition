# Plan replacements
11 Nov 2026: the absent topic 'rateazione e frazionamento del premio' (generali_immagina_adesso) is not absent (document lists instalments). Jobs 833 to 836 now use: {'job-000833': 'arbitrato', 'job-000834': 'coassicurazione', 'job-000835': 'periodo di osservazione', 'job-000836': 'interessi di mora'}.
Topics were checked by synonym search of all Generali chunks (0 real hits). Each gets angle 5 (cap 5 per topic kept). Context chunks unchanged. Old versions: plan/replaced_jobs_archive.jsonl.
jobs.jsonl sha256 before: 3cedeaa29328877d61caeb535eb685c713f6a15417d0a3ac9e181f6030c880a3
jobs.jsonl sha256 after:  96a9083bdcb69d8aa995a5cf56aab2cd56a6b8d6d895d6ab41f84999dfe60eb7
Re-running plan.py no longer reproduces jobs.jsonl; re-apply this script afterwards.

## Applied 1 replacement(s)
- job-000835: 'periodo di osservazione' -> 'duplicato della polizza'
- Reason for 'rateazione e frazionamento del premio': document lists instalments (rate mensili, trimestrali, semestrali); found by blind pass on bulk batch 1
- Reason for 'periodo di osservazione': document has a 'Termine di aspettativa' (waiting period) for natural events; found by blind pass on the replacements
jobs.jsonl sha256 before: 96a9083bdcb69d8aa995a5cf56aab2cd56a6b8d6d895d6ab41f84999dfe60eb7
jobs.jsonl sha256 after:  8539e3907c8925f3fe61467df5acde33877d0efdafb40bf3c7aee01d529fe599
Re-running plan.py does not reproduce jobs.jsonl; re-apply this script afterwards. Each new topic: synonym search of all Generali chunks, 0 real hits; angle 5 (cap 5 kept).

## Applied 15 replacement(s)
- job-000260: 'cambio del piano o della forma di copertura' -> 'coassicurazione'
- job-000285: 'giorni di tolleranza per il pagamento' -> 'risoluzione per decesso del contraente'
- job-000286: 'giorni di tolleranza per il pagamento' -> 'premio minimo'
- job-000299: 'periodo di osservazione' -> 'bonus e sconti per assenza di sinistri'
- job-000748: 'affitti brevi e locazione turistica' -> 'piscina e impianti sportivi'
- job-000751: 'arbitrato' -> 'trasferimento della polizza a un nuovo titolare'
- job-000804: 'lavori di ristrutturazione e appaltatori' -> 'domotica e dispositivi smart'
- job-000813: 'periodo di osservazione' -> 'trasferimento della polizza a un nuovo titolare'
- job-000814: 'periodo di osservazione' -> 'risoluzione per decesso del contraente'
- job-000815: 'periodo di osservazione' -> 'risoluzione per decesso del contraente'
- job-000837: 'riattivazione della polizza' -> 'polizza in valuta estera'
- job-000839: 'riattivazione della polizza' -> 'polizza collettiva o convenzione aziendale'
- job-000843: 'rimborso del premio non goduto' -> 'premio minimo'
- job-000844: 'rimborso del premio non goduto' -> 'lingua del contratto'
- job-001931: 'rimborso del premio non goduto' -> 'risoluzione per decesso del contraente'
- Reason for 'rateazione e frazionamento del premio': document lists instalments (rate mensili, trimestrali, semestrali); found by blind pass on bulk batch 1
- Reason for 'periodo di osservazione': document has a 'Termine di aspettativa' (waiting period) for natural events; found by blind pass on the replacements
- Reason for 'affitti brevi e locazione turistica': blind pass absent3: borderline answerable
- Reason for 'lavori di ristrutturazione e appaltatori': blind pass absent3: answerable
- Reason for 'arbitrato': blind pass absent3: borderline answerable
- Reason for 'periodo di osservazione': blind pass absent3: waiting period exists under another name
- Reason for 'riattivazione della polizza': blind pass absent3: answerable
- Reason for 'rimborso del premio non goduto': blind pass absent3: answerable
- Reason for 'giorni di tolleranza per il pagamento': blind pass absent3: answerable
- Reason for 'cambio del piano o della forma di copertura': blind pass bulk2: document allows written policy changes
jobs.jsonl sha256 before: 8539e3907c8925f3fe61467df5acde33877d0efdafb40bf3c7aee01d529fe599
jobs.jsonl sha256 after:  b6961542bcdc4500889273f747d7422bf15c30e9b61702012d0e6195b9f3e4fa
Re-running plan.py does not reproduce jobs.jsonl; re-apply this script afterwards. Each new topic: synonym search of all Generali chunks, 0 real hits; angle 5 (cap 5 kept).
