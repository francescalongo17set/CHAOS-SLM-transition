"""Step 1 (Kaggle or local, internet on): collect source passages for query generation and record what was found.

Outputs in --out:
  insurance_passages.jsonl   D.Lgs. 209/2005 articles + Civil Code arts. 1882-1932 (+ other insurance laws)
  legal_other_passages.jsonl ITA-CaseHold summaries (legal, NOT insurance) -> out-of-scope-but-legal seeds
  corpus_check.json          proof that the laws we expected are really in the datasets
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so `orch` imports without install
import argparse
import csv
import io
import json
import random
import re
import zipfile
import xml.etree.ElementTree as ET

from huggingface_hub import hf_hub_download

NS = "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}"
NORMATTIVA = "diatribe00/normattiva-lab-data"
CHUNK = 1400


def clean(s):
    return re.sub(r"\s+", " ", s.replace("((", "").replace("))", "")).strip()  # (( )) marks amendments in Normattiva


def cut(s, n=CHUNK):
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0]


def codice_assicurazioni(check):
    zp = hf_hub_download(NORMATTIVA, "data/raw/Codici_vigente.zip", repo_type="dataset")
    z = zipfile.ZipFile(zp)
    names = [n for n in z.namelist() if "20050907_209" in n and n.endswith(".xml")]
    assert names, "D.Lgs. 209/2005 not found in Codici_vigente.zip"
    root = ET.fromstring(z.read(names[0]))
    title = next((e.get("content") for e in root.iter() if e.get("property") == "eli:title"), "")
    out = []
    for a in root.iter(NS + "article"):
        num = clean("".join(a.find(NS + "num").itertext())) if a.find(NS + "num") is not None else "?"
        text = clean("".join(a.itertext()))
        if len(text) >= 300:
            out.append({"source": "D.Lgs. 209/2005", "ref": num, "text": cut(text)})
    check["codice_assicurazioni_private"] = {"file": names[0], "title": title.strip(), "articles": len(out)}
    return out


def civil_code(check):
    p = hf_hub_download("AndreaSimeri/Italian_Civil_Code", "italian_civil_code_dataset_with_references.csv", repo_type="dataset")
    csv.field_size_limit(10**8)
    out = []
    for r in csv.DictReader(open(p, encoding="utf-8")):
        m = re.fullmatch(r"art(\d+)", r["article_id"])
        if m and 1882 <= int(m.group(1)) <= 1932:  # Title III, Book IV: "Dell'assicurazione"
            out.append({"source": "Codice civile", "ref": f"art. {m.group(1)}", "text": cut(f"{r['article_title']} {r['article_text']}")})
    check["civil_code_insurance_articles"] = len(out)
    return out


# Checked by hand against laws_vigente.jsonl (a title regex also matches accounting directives, so we list URNs).
EXTRA_URNS = {
    "urn:nir:stato:decreto.legislativo:2018-05-21;68": "IDD: distribuzione assicurativa",
    "urn:nir:stato:decreto.legislativo:2020-12-30;187": "IDD: correttivo",
    "urn:nir:stato:decreto.legislativo:2015-05-12;74": "Solvency II",
    "urn:nir:stato:decreto.legislativo:2007-11-06;198": "RC auto: direttiva 2005/14/CE",
    "urn:nir:stato:decreto.del.presidente.della.repubblica:2006-07-18;254": "RC auto: risarcimento diretto",
    "urn:nir:stato:decreto.del.presidente.della.repubblica:1970-11-24;973": "RC auto: regolamento L. 990/1969",
    "urn:nir:stato:decreto.legislativo:1995-03-17;174": "assicurazione vita",
    "urn:nir:stato:decreto.legislativo:1995-03-17;175": "assicurazione danni",
    "urn:nir:stato:decreto.legislativo:2016-11-14;224": "PRIIPs / documenti informativi",
    "urn:nir:stato:decreto.legislativo:2006-05-04;182": "RC notai",
}


def other_insurance_laws(check, rng, chunks=5):
    """Stream the 935 MB in-force JSONL once and keep the listed insurance laws (RC auto, distribution, Solvency II...)."""
    p = hf_hub_download(NORMATTIVA, "data/processed/laws_vigente.jsonl", repo_type="dataset")
    found, out = {}, []
    with open(p, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if d["urn"] in EXTRA_URNS:
                found[d["urn"]] = d
    check["other_insurance_laws"] = {u: {"topic": EXTRA_URNS[u], "present": u in found} for u in EXTRA_URNS}
    for u, d in found.items():
        text = clean(d["text"])
        for _ in range(chunks):
            i = rng.randrange(0, max(1, len(text) - CHUNK))
            out.append({"source": d["title"][:90], "ref": u, "text": cut(text[i:i + CHUNK + 200])})
    return out


def itacasehold(check, n=120, rng=None):
    p = hf_hub_download("itacasehold/itacasehold", "data/train-00000-of-00001-f5930e0acbcdcb7f.parquet", repo_type="dataset")
    import pandas as pd
    df = pd.read_parquet(p)
    rows = [{"source": "ITA-CaseHold", "ref": str(r["materia"]), "text": cut(clean(str(r["summary"])), 900)} for _, r in df.iterrows()]
    check["itacasehold_rows"] = len(rows)
    return rng.sample(rows, min(n, len(rows)))


def write(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/corpus")
    ap.add_argument("--no-extra", action="store_true", help="skip the 935 MB download of other insurance laws")
    ap.add_argument("--seed", type=int, default=13)
    a = ap.parse_args()
    import os
    os.makedirs(a.out, exist_ok=True)
    rng, check = random.Random(a.seed), {}
    ins = codice_assicurazioni(check) + civil_code(check)
    if not a.no_extra:
        ins += other_insurance_laws(check, rng)
    write(f"{a.out}/insurance_passages.jsonl", ins)
    write(f"{a.out}/legal_other_passages.jsonl", itacasehold(check, rng=rng))
    check["insurance_passages"] = len(ins)
    json.dump(check, open(f"{a.out}/corpus_check.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(check, ensure_ascii=False, indent=1))
