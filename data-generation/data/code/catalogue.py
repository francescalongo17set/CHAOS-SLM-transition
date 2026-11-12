"""Stage 3: field lexicon, chunk catalogue, absent candidates, comparable fields (book 15.4)."""
import csv, json, re, unicodedata, collections, itertools
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "catalogue"
CAT.mkdir(exist_ok=True)

LEXICON = {
    "franchigia": ["franchigia", "scoperto"],
    "massimale": ["massimale", "somma assicurata", "limite di indennizzo", "limite di risarcimento"],
    "carenza": ["periodo di carenza", "carenza", "termine di aspettativa"],
    "esclusioni": ["esclusioni", "non sono coperti", "sono esclusi", "non e assicurato", "non sono assicurat"],
    "limite di età": ["età massima", "limite di età", "limiti di età", "età di ingresso"],
    "rimborso": ["rimborso", "rimborsa", "indennizzo", "risarcimento"],
    "decorrenza": ["decorrenza", "entra in vigore", "ha effetto", "effetto dalle ore"],
    "durata": ["durata", "scadenza", "rinnovo"],
    "recesso e disdetta": ["recesso", "disdetta", "recedere"],
    "denuncia del sinistro": ["denuncia del sinistro", "denuncia di sinistro", "termini di denuncia", "denunciare"],
    "assistenza": ["assistenza", "centrale operativa", "numero verde", "struttura organizzativa"],
    # extensions found in the documents
    "pagamento del premio": ["pagamento del premio", "frazionamento", "rate"],
    "validità territoriale": ["validità territoriale", "territorio", "dove vale"],
    "prescrizione": ["prescrizione", "termini di prescrizione"],
    "surrogazione": ["surrogazione", "rivalsa"],
    "dichiarazioni e aggravamento del rischio": ["dichiarazioni del contraente", "aggravamento del rischio", "dichiarazioni inesatte"],
    "tutela legale": ["tutela legale", "spese legali", "spese di resistenza"],
    "diaria": ["diaria"],
    "legge applicabile e foro": ["foro competente", "legge applicabile"],
}

HELD = {"zurich_salute": "Sezione 3 - Assistenza", "generali_immagina_adesso": "Prevenzione e assistenza CASA"}
WHERE = {
    "zurich_salute": {"common": "Sezione 1 - Norme comuni a tutte le garanzie", "main": "Sezione 2 - Protezione Salute", "assist": "Sezione 3 - Assistenza"},
    "generali_immagina_adesso": {"common": "Norme Comuni", "main": "In solidità - Danni ai beni", "assist": "Prevenzione e assistenza CASA",
                                 "furto": "In guardia - Furto Su misura"},
    "zurich_impresa": {"common": "Norme comuni a tutte le garanzie", "main": "Incendio e Danni ai beni", "assist": "Assistenza",
                       "rc": "Responsabilità Civile danni a terzi (R.C.T.)", "furto": "Furto"},
}

# (topic, [terms], where)  -- generic topics a policy normally states
GENERIC = [
    ("sospensione del contratto o della garanzia", ["sospension", "sospendere"], "common"),
    ("riattivazione della polizza", ["riattivazion", "riattivare"], "common"),
    ("cessione del contratto", ["cessione del contratto", "cessione della polizza", "cedere il contratto"], "common"),
    ("bonus e sconti per assenza di sinistri", ["bonus", "sconto fedelta", "sconti"], "common"),
    ("mezzi di pagamento del premio", ["bonifico", "carta di credito", "assegno", "contanti", "addebito diretto", "sdd"], "common"),
    ("rateazione e frazionamento del premio", ["frazionamento", "rateazione", "rateale", "pagamento rateale"], "common"),
    ("interessi di mora", ["interessi di mora", "mora"], "common"),
    ("giorni di tolleranza per il pagamento", ["tolleranza"], "common"),
    ("indicizzazione automatica del premio", ["indicizzazion", "adeguamento automatico"], "common"),
    ("polizza in valuta estera", ["valuta estera", "dollari", "sterline"], "common"),
    ("coassicurazione", ["coassicurazion", "coassicurat"], "common"),
    ("penale per recesso anticipato", ["penale", "penali"], "common"),
    ("rimborso del premio non goduto", ["premio non goduto", "rimborso del premio", "restituzione del premio"], "common"),
    ("duplicato della polizza", ["duplicato", "copia della polizza", "smarrimento della polizza"], "common"),
    ("firma elettronica e firma digitale", ["firma elettronica", "firma digitale", "firma grafometrica", "spid"], "common"),
    ("numero massimo di sinistri per anno", ["numero massimo di sinistri", "sinistri per anno", "sinistri per periodo assicurativo"], "common"),
    ("premio minimo", ["premio minimo", "premio di minimo"], "common"),
    ("esclusione per epidemie e pandemie", ["pandemi", "epidemi"], "main"),
    ("esclusione per terrorismo", ["terrorism", "atti terroristici"], "main"),
    ("esclusione per guerra", ["guerra", "operazioni belliche"], "main"),
    ("mediazione obbligatoria", ["mediazion"], "common"),
    ("arbitrato", ["arbitrato", "arbitro"], "common"),
    ("trasferimento della polizza a un nuovo titolare", ["subentro", "trasferimento del contratto", "nuovo titolare"], "common"),
    ("polizza collettiva o convenzione aziendale", ["polizza collettiva", "convenzione aziendale", "adesione collettiva"], "common"),
    ("risoluzione per decesso del contraente", ["decesso del contraente", "morte del contraente"], "common"),
    ("proroga della copertura", ["proroga"], "common"),
    ("periodo di osservazione", ["periodo di osservazione"], "common"),
    ("comunicazioni in formato elettronico", ["posta elettronica ordinaria", "comunicazioni elettroniche", "sms"], "common"),
    ("lingua del contratto", ["lingua del contratto", "lingua inglese"], "common"),
]
SPECIFIC = {
    "zurich_salute": [
        ("gravidanza e parto", ["gravidanz", "parto", "maternit"], "main"),
        ("fecondazione assistita", ["fecondazione", "procreazione"], "main"),
        ("vaccinazioni", ["vaccin"], "main"),
        ("chirurgia estetica", ["chirurgia estetica", "chirurgia plastica", "estetic"], "main"),
        ("protesi acustiche e apparecchi acustici", ["protesi acustich", "apparecchi acustici"], "main"),
        ("occhiali e lenti a contatto", ["occhial", "lenti a contatto", "lenti correttive"], "main"),
        ("psicoterapia e sostegno psicologico", ["psicoterap", "psicolog"], "main"),
        ("trapianti di organi", ["trapiant"], "main"),
        ("second opinion medica", ["second opinion", "secondo parere"], "main"),
        ("malattie rare", ["malattie rare", "malattia rara"], "main"),
        ("check-up pediatrico", ["pediatric", "neonat"], "main"),
        ("ticket sanitari", ["ticket"], "main"),
        ("assistenza infermieristica domiciliare", ["infermier"], "main"),
        ("indennità di convalescenza", ["convalescenz"], "main"),
        ("lungodegenza e riabilitazione in struttura", ["lungodegenz", "riabilitazion"], "main"),
        ("cure termali", ["termal", "terme"], "main"),
        ("cure oncologiche e chemioterapia", ["oncolog", "chemioterap", "radioterap", "tumor"], "main"),
        ("ortodonzia", ["ortodonz"], "main"),
        ("sport pericolosi o professionistici", ["sport", "paracadut", "alpinismo", "professionistic"], "main"),
        ("copertura per patologie pregresse", ["pregresse", "preesistent"], "main"),
        ("limite di età per l'ingresso", ["eta massima di ingresso", "limite di eta", "limiti di eta", "eta di ingresso"], "common"),
        ("dipendenze da alcol o droghe", ["alcol", "stupefacent", "tossicodipendenz"], "main"),
        ("copertura dei figli maggiorenni", ["figli maggiorenni", "figli a carico", "figli conviventi"], "common"),
        ("cambio del piano o della forma di copertura", ["cambio di forma", "cambio del piano", "passaggio di forma"], "common"),
        ("cure all'estero", ["cure all estero", "ricovero all estero", "istituto di cura estero"], "main"),
        ("invio di una badante o assistente familiare", ["badante", "assistente familiare"], "assist"),
        ("assistenza veterinaria per animali domestici", ["veterinar", "animali domestici", "animale domestico"], "assist"),
        ("rimpatrio della salma", ["salma"], "assist"),
        ("taxi sanitario", ["taxi"], "assist"),
        ("trasferimento in elicottero", ["elicottero", "eliambulanza"], "assist"),
        ("servizio di interprete", ["interprete"], "assist"),
        ("anticipo della cauzione all'estero", ["cauzione"], "assist"),
        ("invio di un baby sitter", ["baby sitter", "babysitter", "baby-sitter"], "assist"),
        ("consegna della spesa a domicilio", ["consegna della spesa", "spesa a domicilio"], "assist"),
        ("servizio di lavanderia o pulizie", ["lavanderia", "colf", "pulizie"], "assist"),
        ("sostegno psicologico telefonico", ["supporto psicologico", "sostegno psicologico", "assistenza psicologica"], "assist"),
        ("prenotazione di visite ed esami", ["prenotazione di visite", "prenotazione delle visite", "prenotazione di esami"], "assist"),
        ("assistenza ai familiari non autosufficienti", ["non autosufficien"], "assist"),
        ("invio di un fisioterapista a domicilio", ["fisioterapista a domicilio", "fisioterapist"], "assist"),
        ("assistenza per smarrimento dei documenti", ["smarrimento dei documenti", "perdita dei documenti"], "assist"),
        ("assistenza legale telefonica all'estero", ["segnalazione di un legale", "legale all estero", "consulenza legale telefonica"], "assist"),
    ],
    "generali_immagina_adesso": [
        ("piscina e impianti sportivi", ["piscina", "campo da tennis"], "main"),
        ("giardino e alberi", ["giardin", "alberi ad alto fusto"], "main"),
        ("animali domestici", ["animali domestici", "animale domestico", "cane", "gatto"], "main"),
        ("opere d'arte e oggetti da collezione", ["opere d arte", "collezion", "quadri"], "main"),
        ("biciclette e monopattini elettrici", ["monopattin", "biciclett"], "main"),
        ("affitti brevi e locazione turistica", ["affitti brevi", "locazione turistica", "airbnb", "b&b"], "main"),
        ("abitazione disabitata", ["disabitat", "inabitat"], "main"),
        ("muffa e umidità", ["muffa", "umidita"], "main"),
        ("danni da animali nocivi", ["roditori", "insetti", "animali nocivi"], "main"),
        ("cantina e box auto", ["box auto", "autorimessa", "garage"], "main"),
        ("ascensore e impianti condominiali", ["ascensore", "montacarichi"], "main"),
        ("pannelli solari e fotovoltaico", ["pannelli solari", "fotovoltaic"], "main"),
        ("domotica e dispositivi smart", ["domotic", "smart home"], "main"),
        ("danni da terremoto", ["terremot", "sisma"], "main"),
        ("danni da alluvione", ["alluvion", "inondazion"], "main"),
        ("furto di biciclette all'esterno", ["biciclette all esterno", "furto di biciclett"], "furto"),
        ("furto di veicoli", ["furto di veicol", "autoveicol"], "furto"),
        ("rapina fuori dall'abitazione con carte di credito", ["carte di credito", "bancomat", "prelievo"], "furto"),
        ("copertura per ospiti e persone di servizio", ["ospiti", "persone di servizio"], "main"),
        ("lavori di ristrutturazione e appaltatori", ["appaltator", "ristrutturazione edilizia"], "main"),
        ("beni in comproprietà", ["comproprieta", "comproprietar"], "main"),
        ("sinistri causati da minori", ["minori di", "minorenni"], "main"),
        ("assistenza veterinaria per animali domestici", ["veterinar", "animali domestici", "animale domestico"], "assist"),
        ("servizio di interprete", ["interprete"], "assist"),
        ("invio di un'ambulanza", ["ambulanza"], "assist"),
        ("taxi in caso di emergenza", ["taxi"], "assist"),
        ("consulenza medica telefonica", ["consulenza medica", "pediatra", "medico di guardia"], "assist"),
        ("invio di un giardiniere", ["giardinier"], "assist"),
        ("assistenza informatica a domicilio", ["informatic", "computer"], "assist"),
        ("invio di un baby sitter o pet sitter", ["baby sitter", "babysitter", "pet sitter"], "assist"),
        ("consegna della spesa a domicilio", ["consegna della spesa", "spesa a domicilio"], "assist"),
        ("assistenza per smarrimento dei documenti", ["smarrimento dei documenti", "perdita dei documenti"], "assist"),
        ("invio di un muratore o piastrellista", ["muratore", "piastrellist", "imbianchin"], "assist"),
        ("invio di un tecnico per la caldaia", ["caldaia", "termotecnic", "climatizzat"], "assist"),
        ("consulenza legale telefonica", ["consulenza legale", "assistenza legale"], "assist"),
        ("rientro anticipato per animali", ["rientro dell animale"], "assist"),
    ],
    "zurich_impresa": [
        ("cyber risk e attacchi informatici", ["cyber", "attacco informatico", "attacchi informatici", "hacker"], "main"),
        ("merci in transito e trasporto", ["merci in transito", "trasporto merci", "merci trasportate"], "main"),
        ("valuta estera e crediti insoluti", ["valuta estera", "crediti insoluti", "insolvenza dei clienti"], "main"),
        ("smart working e lavoro agile", ["smart working", "lavoro agile"], "main"),
        ("portavalori e trasporto di denaro", ["portavalori", "trasporto di denaro", "trasporto valori"], "furto"),
        ("inquinamento accidentale", ["inquinament"], "rc"),
        ("responsabilità degli amministratori", ["amministratori e dirigenti", "d&o", "responsabilita degli amministratori"], "rc"),
        ("serre e coltivazioni agricole", ["serre", "colture", "agricol"], "main"),
        ("veicoli dei dipendenti in parcheggio", ["veicoli dei dipendenti", "auto dei dipendenti", "parcheggio aziendale"], "rc"),
        ("danni da interruzione di energia elettrica", ["interruzione di energia", "black out", "blackout", "mancanza di energia"], "main"),
        ("beni in leasing", ["leasing", "locazione finanziaria"], "main"),
        ("beni di terzi in uso o comodato", ["comodato", "beni in uso"], "main"),
        ("fiere, mostre ed esposizioni", ["fiere", "mostre", "esposizioni"], "main"),
        ("lavoratori autonomi e collaboratori esterni", ["collaboratori esterni", "lavoratori autonomi", "stagisti", "tirocinant"], "rc"),
        ("danni da terremoto", ["terremot", "sisma"], "main"),
        ("danni da alluvione e inondazione", ["alluvion", "inondazion"], "main"),
        ("perdita di dati e software", ["perdita di dati", "ricostruzione dei dati", "software"], "main"),
        ("furto di merci a bordo di veicoli", ["a bordo di veicol", "furto di merci in veicol"], "furto"),
        ("rapina in banca o agenzia", ["agenzia di banca", "rapina in banca"], "furto"),
        ("danni da amianto", ["amianto", "asbesto"], "main"),
        ("responsabilità per beni consegnati in deposito", ["beni in deposito", "cose in consegna"], "rc"),
        ("danni all'immagine e reputazione", ["reputazione", "immagine aziendale", "danno di immagine"], "rc"),
        ("sanzioni amministrative", ["sanzioni amministrative"], "rc"),
        ("danni da incendio doloso del contraente", ["incendio doloso"], "main"),
        ("rischi ambientali e bonifica", ["bonifica", "ripristino ambientale"], "rc"),
        ("danni da droni", ["drone", "droni", "aeromobil"], "rc"),
        ("assistenza informatica d'urgenza", ["assistenza informatica", "pronto intervento informatico"], "assist"),
        ("invio di un medico in azienda", ["invio di un medico", "medico in azienda"], "assist"),
        ("ritorno anticipato dei dipendenti", ["rientro anticipato", "rimpatrio dei dipendenti"], "assist"),
        ("interprete per trasferte di lavoro", ["interprete"], "assist"),
        ("vigilanza e sorveglianza dopo il sinistro", ["sorveglianza", "vigilanza"], "assist"),
        ("impresa di pulizie dopo un sinistro", ["impresa di pulizie", "pulizie straordinarie"], "assist"),
        ("trasloco temporaneo dell'attività", ["trasloco", "ricollocazione dell attivita"], "assist"),
    ],
}

BAD = re.compile("[  \u0085]")


def n(s):
    s = unicodedata.normalize("NFKD", s.lower()).replace("’", " ").replace("'", " ").replace("-", " ")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9&]+", " ", s).strip()


def term_re(t):
    return re.compile(r"\b" + re.escape(n(t)))


VALUE = re.compile(r"(?:€\s*\d|\d[\d\.,]*\s*(?:€|euro|%|per cento|giorn[io]|mes[ei]|ann[io])\b)", re.I)
COND = re.compile(r"\bse\b|\bqualora\b|\bpurch[eé]\b|a condizione che|\bsalvo\b|\btranne\b", re.I)
LISTLINE = re.compile(r"^\s*(?:[•\-–▪●]|\(?[a-z0-9]{1,2}[\)\.])\s")


def main():
    (CAT / "field_lexicon.yaml").write_text(yaml.safe_dump(LEXICON, allow_unicode=True, sort_keys=False), encoding="utf-8")
    lex_re = {f: [term_re(t) for t in ts] for f, ts in LEXICON.items()}
    chunks = [json.loads(l) for l in open(ROOT / "chunks/chunks.jsonl", encoding="utf-8")]
    absent_sections = {}
    cat = []
    for c in chunks:
        tn = n(c["text"])
        fields = [f for f, rs in lex_re.items() if any(r.search(tn) for r in rs)]
        has_value = bool(VALUE.search(c["text"]))
        has_cond = bool(COND.search(c["text"]))
        is_list = sum(bool(LISTLINE.match(x)) for x in c["text"].split("\n")) >= 3
        use = []
        if has_value:  # relaxed from "exactly one field" (book 15.4): see logs/gate_G1.md
            use.append("single_value")
        if has_value and has_cond:
            use.append("conditional")
        if is_list or len(fields) >= 2:
            use.append("multi_fact")
        cat.append({"chunk_id": c["chunk_id"], "doc_id": c["doc_id"], "pool": c["pool"], "top_section": c["top_section"],
                    "coverage": c["section_path"].split(" > ")[-1], "fields_found": fields, "has_value": has_value,
                    "has_condition": has_cond, "is_list": is_list, "n_fields": len(fields), "usable_for": use,
                    "is_table": c["is_table"], "page": c["page"], "n_chars": c["n_chars"]})
    with open(CAT / "chunk_catalogue.jsonl", "w", encoding="utf-8") as f:
        for r in cat:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- absent candidates (zero-hit keyword search on the whole extracted text) ----
    flagged = collections.defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/page_report.csv")):
        if r["flag"]:
            flagged[r["doc_id"]].append(int(r["page"]))
    rows = []
    for doc in ["zurich_salute", "generali_immagina_adesso", "zurich_impresa"]:
        text = n(" \n ".join(json.loads(l)["text"] for l in open(ROOT / f"extracted/{doc}.jsonl", encoding="utf-8")))
        topics = GENERIC + SPECIFIC[doc]
        seen = set()
        for topic, terms, where in topics:
            if topic in seen:
                continue
            seen.add(topic)
            hits = sum(len(term_re(t).findall(text)) for t in terms)
            where_sec = WHERE[doc].get(where) or WHERE[doc]["main"]
            if doc == "zurich_impresa":
                split = "test"
            else:
                split = "validation" if where == "assist" else "train"
            rows.append({"doc_id": doc, "topic": topic, "terms_searched": "; ".join(terms), "hits": hits, "expected_section": where_sec,
                         "flagged_pages": " ".join(map(str, flagged.get(doc, []))), "confirmed": "false", "split": split,
                         "usable": "true" if hits == 0 else "false"})
    with open(CAT / "absent_candidates.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---- comparable fields ----
    pairs = {
        "train": (lambda c: c["doc_id"] == "zurich_salute" and c["pool"] == "train_pool", lambda c: c["doc_id"] == "generali_immagina_adesso" and c["pool"] == "train_pool"),
        "validation": (lambda c: c["doc_id"] == "zurich_salute" and c["pool"] == "validation_pool", lambda c: c["doc_id"] == "generali_immagina_adesso" and c["pool"] == "validation_pool"),
        "test": (lambda c: c["doc_id"] == "zurich_impresa", lambda c: c["doc_id"] == "generali_immagina_adesso" and c["pool"] == "train_pool"),
    }
    cmp_rows = []
    for split, (fa, fb) in pairs.items():
        A, B = [c for c in cat if fa(c)], [c for c in cat if fb(c)]
        for fld in LEXICON:
            a = [c for c in A if fld in c["fields_found"]]
            b = [c for c in B if fld in c["fields_found"]]
            if a and b:
                cmp_rows.append({"split": split, "field": fld, "chunks_a": len(a), "chunks_b": len(b), "chunk_pairs": len(a) * len(b),
                                 "doc_a": A[0]["doc_id"], "doc_b": B[0]["doc_id"]})
    with open(CAT / "comparable_fields.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cmp_rows[0].keys()))
        w.writeheader()
        w.writerows(cmp_rows)

    # ---- summary ----
    out = ["# Catalogue summary (stage 3)\n", "## Usable chunks per document, pool and question type\n",
           "| doc | pool | chunks | single_value | conditional | multi_fact | list/table chunks |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for doc in ["zurich_salute", "generali_immagina_adesso", "zurich_impresa"]:
        for pool in ["train_pool", "validation_pool", "test_pool"]:
            sub = [c for c in cat if c["doc_id"] == doc and c["pool"] == pool]
            if not sub:
                continue
            cnt = collections.Counter(u for c in sub for u in c["usable_for"])
            out.append(f"| {doc} | {pool} | {len(sub)} | {cnt['single_value']} | {cnt['conditional']} | {cnt['multi_fact']} | {sum(c['is_list'] for c in sub)} / {sum(c['is_table'] for c in sub)} |")
    dem = {("zurich_salute", "train_pool"): (128, 80, 48, 3), ("generali_immagina_adesso", "train_pool"): (212, 132, 80, 3),
           ("zurich_salute", "validation_pool"): (30, 19, 11, 3), ("generali_immagina_adesso", "validation_pool"): (30, 19, 11, 3),
           ("zurich_impresa", "test_pool"): (200, 125, 75, 2)}
    out += ["\n## Capacity of value-bearing chunks vs demand (single_value + conditional)\n",
            "| doc | pool | value chunks | demand | base cap | capacity at base | share of capacity | ladder step needed |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    for (doc, pool), (s_, c_, m_, cap) in dem.items():
        hv = sum(1 for c in cat if c["doc_id"] == doc and c["pool"] == pool and c["has_value"])
        need = s_ + c_
        cap_now = hv * cap
        step = "none (70% rule)" if need <= 0.7 * cap_now else "1: 100% at base cap" if need <= cap_now else \
            f"2: cap {cap+1}" if need <= hv * (cap + 1) else f"3: cap {cap+2}" if need <= hv * (cap + 2) else "4/5: move to other doc or stop"
        out.append(f"| {doc} | {pool} | {hv} | {need} | {cap} | {cap_now} | {100*need/cap_now:.0f}% | {step} |")
    out += ["\n## Absent topics (zero hits, usable)\n", "| doc | split | usable topics | max absent questions (5 per topic) | planned absent quota |", "| --- | --- | ---: | ---: | ---: |"]
    quota = {("zurich_salute", "train"): 64, ("generali_immagina_adesso", "train"): 106, ("zurich_salute", "validation"): 15,
             ("generali_immagina_adesso", "validation"): 15, ("zurich_impresa", "test"): 100}
    for (doc, sp), q in quota.items():
        k = sum(1 for r in rows if r["doc_id"] == doc and r["split"] == sp and r["usable"] == "true")
        out.append(f"| {doc} | {sp} | {k} | {5*k} | {q} |")
    out += ["\n## Comparable fields (fields found on both sides)\n", "| split | fields | thresholds (8/4/8) |", "| --- | ---: | --- |"]
    thr = {"train": 8, "validation": 4, "test": 8}
    for sp in ["train", "validation", "test"]:
        fl = [r["field"] for r in cmp_rows if r["split"] == sp]
        out.append(f"| {sp} | {len(fl)}: {', '.join(fl)} | {'OK' if len(fl) >= thr[sp] else 'BELOW'} |")
    (CAT / "catalogue_summary.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
