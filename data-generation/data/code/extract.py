"""Stage 1: extract text of the three chunked PDFs (guideline book 15.1).

Output: extracted/<doc_id>.jsonl (one line per page), extracted/page_report.csv,
extracted/toc_<doc_id>.json (PDF outline, if any).
Only the three chunked documents are read; the two IBIP PDFs are never opened.
"""
import csv, json, re, sys, unicodedata, collections
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "raw", ROOT / "extracted"
OUT.mkdir(exist_ok=True)

DOCS = {
    "zurich_salute": ("ZURICH-Zurich_Salute-SET_INFORMATIVO-ad05f1.pdf", 53),
    "generali_immagina_adesso": ("Generali-Immagina_Adesso-SET_INFORMATIVO-29a54c.pdf", 140),
    "zurich_impresa": ("ZURICH-Zurich_Impresa-SET_INFORMATIVO-8435ac.pdf", 188),
}
BAD = re.compile("[  \u0085]")
BULLET = re.compile(r"^\s*(?:[•\-–▪●○◦■□]|\(?[a-z0-9]{1,2}[\)\.]\s|\d+(?:\.\d+)*\s)")
PAGENUM = re.compile(r"(?:\bpag(?:ina|\.)?\s*\d+\s*(?:di|/)\s*\d*|^\s*\d+\s+di\s+\d+|^\s*-?\s*\d{1,3}\s*-?\s*$)", re.I)
MARGIN = 0.08


def norm(s):
    s = unicodedata.normalize("NFC", BAD.sub(" ", s))
    s = s.replace("­", "").replace("\t", " ").replace("\xa0", " ")
    return re.sub(r" {2,}", " ", s).strip()


def digits_off(s):
    return re.sub(r"\d+", "#", norm(s).lower())


def page_lines(page):
    """Return text blocks: dict(bbox, lines=[(text,size,bold)], size, bold)."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b["type"] != 0:
            continue
        lines = []
        for l in b["lines"]:
            txt = "".join(s["text"] for s in l["spans"])
            if not txt.strip():
                continue
            sizes = [s["size"] for s in l["spans"] if s["text"].strip()]
            bold = [bool(s["flags"] & 16) or "bold" in s["font"].lower() for s in l["spans"] if s["text"].strip()]
            lines.append((txt, max(sizes), sum(bold) / len(bold) > 0.6, tuple(round(x, 1) for x in l["bbox"])))
        if lines:
            out.append({"bbox": b["bbox"], "lines": lines, "kind": "text"})
    return out


def order_blocks(blocks, W):
    """Reading order; two columns detected from narrow blocks on both sides."""
    narrow = [b for b in blocks if (b["bbox"][2] - b["bbox"][0]) < 0.55 * W]
    left = [b for b in narrow if b["bbox"][2] <= 0.56 * W]
    right = [b for b in narrow if b["bbox"][0] >= 0.44 * W]
    overlap = sum(1 for a in left for c in right if min(a["bbox"][3], c["bbox"][3]) - max(a["bbox"][1], c["bbox"][1]) > 5)
    if len(left) >= 3 and len(right) >= 3 and overlap >= 3:
        full = sorted([b for b in blocks if b not in left and b not in right], key=lambda b: b["bbox"][1])
        def key(b):
            if b in left or b in right:
                k = sum(1 for f in full if f["bbox"][1] < b["bbox"][1])
                return (2 * k - 1, 1 if b in left else 2, b["bbox"][1])
            return (2 * full.index(b), 0, b["bbox"][1])
        for b in blocks:
            b["two_col"] = b in left or b in right
        return sorted(blocks, key=key), True
    return sorted(blocks, key=lambda b: (round(b["bbox"][1] / 3), b["bbox"][0])), False


def merge_lines(lines):
    """Join lines of a paragraph; keep list items and heading-like lines apart; join hyphen breaks.
    Returns list of dict(t, size, bold)."""
    out = []
    prev_short = False
    for txt, size, bold, _bb in lines:
        t = norm(txt)
        if not t:
            continue
        starts_new = prev_short and t[:1].isupper()
        prev_short = len(t.split()) <= 8 and not re.search(r"[.;:,]$", t)
        if out and not BULLET.match(t) and not starts_new:
            prev = out[-1]
            same_style = prev["bold"] == bold and abs(prev["size"] - size) < 1.0
            if same_style:
                if re.search(r"[A-Za-zÀ-ÿ]-$", prev["t"]) and t[:1].islower():
                    prev["t"] = prev["t"][:-1] + t
                    continue
                if not re.search(r"[:;]$", prev["t"]) or t[:1].islower():
                    prev["t"] += " " + t
                    continue
        out.append({"t": t, "size": round(size, 1), "bold": bold})
    return out


def extract_doc(doc_id, fname, expect):
    d = fitz.open(RAW / fname)
    assert len(d) == expect, (doc_id, len(d), expect)
    toc = d.get_toc()
    (OUT / f"toc_{doc_id}.json").write_text(json.dumps(toc, ensure_ascii=False))
    pages = []
    for pn, page in enumerate(d, 1):
        W, H = page.rect.width, page.rect.height
        blocks = page_lines(page)
        tables = []
        try:
            for t in page.find_tables().tables:
                ys = [(r.bbox[1], r.bbox[3]) for r in t.rows]
                xs = []
                for c in t.cells:
                    if c is not None and not any(abs(c[0] - x) < 4 for x in xs):
                        xs.append(c[0])
                xs.sort()
                grid = collections.defaultdict(list)
                for blk in blocks:
                    for ln in blk["lines"]:
                        bb = ln[3]
                        cy = (bb[1] + bb[3]) / 2
                        if not (t.bbox[0] - 2 <= (bb[0] + bb[2]) / 2 <= t.bbox[2] + 2 and t.bbox[1] - 2 <= cy <= t.bbox[3] + 2):
                            continue
                        ri = next((i for i, (y0, y1) in enumerate(ys) if y0 - 1 <= cy <= y1 + 1), None)
                        if ri is None:
                            continue
                        ci = max([i for i, x in enumerate(xs) if x <= bb[0] + 3] or [0])
                        grid[(ri, ci)].append((bb[1], bb[0], norm(ln[0])))
                rows = []
                for ri in range(len(ys)):
                    row = [" ".join(g[2] for g in sorted(grid.get((ri, ci), []))) for ci in range(len(xs))]
                    if any(row):
                        rows.append(row)
                if len(rows) >= 2 and len(xs) >= 2:
                    tables.append((t.bbox, rows))
        except Exception:
            pass
        kept = []
        for b in blocks:
            cx, cy = (b["bbox"][0] + b["bbox"][2]) / 2, (b["bbox"][1] + b["bbox"][3]) / 2
            if any(t[0][0] - 2 <= cx <= t[0][2] + 2 and t[0][1] - 2 <= cy <= t[0][3] + 2 for t in tables):
                continue
            kept.append(b)
        for bbox, rows in tables:
            kept.append({"bbox": bbox, "kind": "table", "rows": rows,
                         "lines": [(" | ".join(c for c in r), 9.0, False, tuple(bbox)) for r in rows]})
        ordered, two_col = order_blocks(kept, W)
        pages.append({"doc_id": doc_id, "page": pn, "W": W, "H": H, "blocks": ordered, "two_col": two_col, "n_tables": len(tables)})
    return pages, toc


def strip_margins(pages):
    """Remove repeating header/footer lines and page-number lines in the top/bottom 8%."""
    n = len(pages)
    cnt = collections.Counter()
    for p in pages:
        seen = set()
        for b in p["blocks"]:
            for txt, sz, bd, bb in b["lines"]:
                if bb[1] < MARGIN * p["H"] or bb[3] > (1 - MARGIN) * p["H"]:
                    seen.add(digits_off(txt))
        cnt.update(seen)
    repeated = {k for k, v in cnt.items() if v >= min(0.30 * n, 10) and k}
    removed = collections.Counter()
    for p in pages:
        for b in p["blocks"]:
            if b["kind"] == "table":
                continue
            keep = []
            for ln in b["lines"]:
                txt, sz, bd, bb = ln
                inmargin = bb[1] < MARGIN * p["H"] or bb[3] > (1 - MARGIN) * p["H"]
                k = digits_off(txt)
                if inmargin and (k in repeated or PAGENUM.search(norm(txt))):
                    removed[k] += 1
                    continue
                keep.append(ln)
            b["lines"] = keep
        p["blocks"] = [b for b in p["blocks"] if b["lines"]]
    return removed


def finalize(p):
    blocks = []
    for b in p["blocks"]:
        if b["kind"] == "table":
            ls = [{"t": " | ".join(r), "size": 9.0, "bold": False} for r in b["rows"]]
        else:
            ls = merge_lines(b["lines"])
        if not ls:
            continue
        blocks.append({"kind": b["kind"], "bbox": [round(x, 1) for x in b["bbox"]], "lines": ls})
    text = "\n".join(l["t"] for b in blocks for l in b["lines"])
    return {"doc_id": p["doc_id"], "page": p["page"], "text": text, "blocks": blocks,
            "two_col": p["two_col"], "n_tables": p["n_tables"]}


def main():
    rep = []
    for doc_id, (fname, expect) in DOCS.items():
        pages, toc = extract_doc(doc_id, fname, expect)
        removed = strip_margins(pages)
        recs = [finalize(p) for p in pages]
        with open(OUT / f"{doc_id}.jsonl", "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        for r in recs:
            nch = len(r["text"])
            rep.append({"doc_id": doc_id, "page": r["page"], "characters": nch,
                        "flag": "low_text" if nch < 200 else "", "two_col": int(r["two_col"]), "tables": r["n_tables"]})
        low = sum(1 for r in recs if len(r["text"]) < 200)
        print(f"{doc_id}: pages={len(recs)} low_text={low} ({100*low/len(recs):.1f}%) two_col={sum(r['two_col'] for r in recs)} "
              f"tables={sum(r['n_tables'] for r in recs)} toc={len(toc)} chars={sum(len(r['text']) for r in recs)}")
        print("  margin lines removed (top):", removed.most_common(4))
    with open(OUT / "page_report.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["doc_id", "page", "characters", "flag", "two_col", "tables"])
        w.writeheader(); w.writerows(rep)


if __name__ == "__main__":
    main()
