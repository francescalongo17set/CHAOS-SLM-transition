"""Stage 2: headings, section paths and chunks (guideline book 15.2 and 15.3).

Reads extracted/<doc_id>.jsonl (+ toc for Generali). Writes chunks/chunks.jsonl,
chunks/headings_<doc_id>.csv and chunks/chunk_report.md.
"""
import csv, json, re, unicodedata, collections, random, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXT, OUT = ROOT / "extracted", ROOT / "chunks"
OUT.mkdir(exist_ok=True)
SEED = 20261110

META = {
    "zurich_salute": ("Zurich", "Salute", "health"),
    "generali_immagina_adesso": ("Generali", "Immagina Adesso", "home"),
    "zurich_impresa": ("Zurich", "Impresa", "multi-risk business"),
}
# front matter: (first page, top section label); ladder (font-based headings) starts at ladder_start
CONFIG = {
    "zurich_salute": {"front": [(1, "Copertina"), (2, "DIP"), (4, "DIP aggiuntivo")], "ladder_start": 7, "mode": "ladder"},
    "zurich_impresa": {"front": [(1, "Copertina"), (2, "DIP"), (5, "DIP aggiuntivo")], "ladder_start": 57, "mode": "ladder"},
    "generali_immagina_adesso": {"front": [(1, "Copertina"), (3, "DIP"), (None, "DIP aggiuntivo")], "ladder_start": 19, "mode": "toc"},
}
DROP_SECTIONS = {"Copertina", "Frontespizio", "Indice"}
HELD_OUT = {"zurich_salute": "Sezione 3", "generali_immagina_adesso": "Prevenzione e assistenza CASA"}

TARGET, SOFT_MAX, LONG_PARA, OVERLAP_MIN, OVERLAP_MAX, TAIL_MIN, HARD_MAX, HEAD_BREAK_MIN = 1500, 1800, 2200, 100, 200, 300, 2400, 600
BAD = re.compile("[  \u0085]")
BLANK = re.compile(r"lasciata intenzionalmente bianca", re.I)


def n(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def load(doc_id):
    lines = []
    for l in open(EXT / f"{doc_id}.jsonl", encoding="utf-8"):
        r = json.loads(l)
        for bi, b in enumerate(r["blocks"]):
            for ri, x in enumerate(b["lines"]):
                if BLANK.search(x["t"]):
                    continue
                lines.append({"page": r["page"], "t": x["t"], "size": x["size"], "bold": x["bold"],
                              "kind": b["kind"], "block": (r["page"], bi), "level": None, "title": None})
    return lines


def words(t):
    return len(t.split())


def is_short_title(t):
    return words(t) <= 14 and not re.search(r"[.:;,]$", t)


def mark_ladder(doc_id, lines, cfg):
    """Zurich: font-size ladder. L1 >=24pt, L2 16pt, L3 12pt (clause titles). Front pages: bold headings."""
    prev = None
    for ln in lines:
        if ln["kind"] != "text":
            prev = None
            continue
        t, sz, bd, p = ln["t"], ln["size"], ln["bold"], ln["page"]
        if p >= cfg["ladder_start"]:
            if sz >= 24 and words(t) <= 14:
                ln["level"] = 1
            elif sz == 16.0 and not bd and is_short_title(t):
                ln["level"] = 2
            elif sz == 12.0 and not bd and is_short_title(t):
                ln["level"] = 3
        else:
            if bd and sz >= 10.9 and is_short_title(t) and p >= 2:
                ln["level"] = 2
            elif bd and 9.0 <= sz <= 9.5 and (t.isupper() or (words(t) <= 6 and not re.search(r"[.:;,?]$", t))) and words(t) <= 8 and p >= 5 and cfg["front"][-1][0] and p >= cfg["front"][-1][0]:
                ln["level"] = 3 if len(t) > 3 else None
    # merge consecutive L1 lines (Sezione 3 + Assistenza)
    out = []
    for ln in lines:
        if ln["level"] == 1 and out and out[-1]["level"] == 1 and out[-1]["page"] == ln["page"]:
            a = out[-1]
            sep = " - " if re.match(r"^(Sezione|Allegato) \d+$", a["t"]) else " "
            a["t"] = a["t"] + sep + ln["t"]
            continue
        out.append(ln)
    for ln in out:
        if ln["level"]:
            ln["title"] = ln["t"]
    return out


def mark_toc(doc_id, lines, cfg):
    toc = json.load(open(EXT / f"toc_{doc_id}.json"))
    by_page = collections.defaultdict(list)
    for i, ln in enumerate(lines):
        by_page[ln["page"]].append(i)
    synth = collections.defaultdict(list)  # line index -> synthetic headings before it
    miss = 0
    last = 0
    for lvl, title, page in toc:
        if page < cfg["ladder_start"]:
            continue
        title_clean = re.sub(r"\s+", " ", title).strip()
        key = n(title_clean)
        found = None
        for pg in (page, page + 1):
            for i in by_page.get(pg, []):
                if i < last or lines[i]["level"]:
                    continue
                ln = n(lines[i]["t"])
                if lines[i]["kind"] == "text" and key and (ln == key or (key in ln and len(ln) <= len(key) + 24)):
                    found = i
                    break
            if found is not None:
                break
        if found is None:
            miss += 1
            first = by_page.get(page, [None])[0]
            if first is None:
                continue
            first = max(first, last)
            synth[first].append((lvl, title_clean))
        else:
            lines[found]["level"], lines[found]["title"] = lvl, title_clean
            last = found
    return synth, miss


def find_dipa_start(lines):
    for ln in lines:
        if 4 <= ln["page"] < 19 and re.search(r"DIP\s+aggiuntivo", ln["t"], re.I) and ln["bold"]:
            return ln["page"]
    return None


def sentences(t):
    return [s for s in re.split(r"(?<=[.!?])\s+", t) if s]


def split_long(text, page):
    out = []
    while len(text) > LONG_PARA:
        best, bd = None, 10**9
        for m in re.finditer(r"(?<=[.!?;])\s+", text):
            d = abs(m.end() - TARGET)
            if d < bd and m.end() >= 600:
                best, bd = m.end(), d
        if best is None:
            best = text.rfind(" ", 0, TARGET) + 1 or TARGET
        out.append(text[:best].strip())
        text = text[best:].strip()
    out.append(text)
    return out


def make_units(items):
    """items: list of line dicts (with path/level) of one top section -> units."""
    units = []
    i = 0
    while i < len(items):
        ln = items[i]
        if ln["kind"] == "table":
            rows = []
            blk = ln["block"]
            j = i
            while j < len(items) and items[j]["kind"] == "table" and items[j]["block"] == blk:
                rows.append(items[j])
                j += 1
            exp = []
            for r in rows:
                if len(r["t"]) > LONG_PARA:
                    for pc in split_long(r["t"], r["page"]):
                        exp.append(dict(r, t=pc))
                else:
                    exp.append(r)
            rows = exp
            total = sum(len(r["t"]) + 1 for r in rows)
            if total <= SOFT_MAX:
                units.append({"text": "\n".join(r["t"] for r in rows), "page": rows[0]["page"], "level": None,
                              "path": rows[0]["path"], "table": True, "cs": rows[0]["cs"], "ce": rows[-1]["ce"]})
            else:
                if len(rows[0]["t"]) <= 500:
                    header, body = rows[0], rows[1:]
                else:
                    header, body = None, rows
                hl = [header["t"]] if header else []
                part, plen = [], 0
                for r in body:
                    if part and plen + len(r["t"]) + 1 > TARGET:
                        units.append({"text": "\n".join(hl + [x["t"] for x in part]), "page": part[0]["page"], "level": None,
                                      "path": part[0]["path"], "table": True, "cs": part[0]["cs"], "ce": part[-1]["ce"]})
                        part, plen = [], 0
                    part.append(r)
                    plen += len(r["t"]) + 1
                if part:
                    units.append({"text": "\n".join(hl + [x["t"] for x in part]), "page": part[0]["page"], "level": None,
                                  "path": part[0]["path"], "table": True, "cs": (header or part[0])["cs"] if len(units) == 0 else part[0]["cs"], "ce": part[-1]["ce"]})
            i = j
            continue
        pieces = split_long(ln["t"], ln["page"]) if len(ln["t"]) > LONG_PARA else [ln["t"]]
        pos = ln["cs"]
        for pc in pieces:
            units.append({"text": pc, "page": ln["page"], "level": ln["level"], "path": ln["path"], "table": False,
                          "cs": pos, "ce": pos + len(pc)})
            pos += len(pc) + 1
        i += 1
    return units


def assemble(units):
    chunks, cur = [], []

    def clen(c):
        return sum(len(u["text"]) + 1 for u in c)

    def close():
        nonlocal cur
        carry = []
        while len(cur) > 1 and cur[-1]["level"]:
            carry.insert(0, cur.pop())
        if cur:
            chunks.append(cur)
        cur = carry

    for u in units:
        L = len(u["text"]) + 1
        if cur and (clen(cur) + L > SOFT_MAX or (u["level"] and u["level"] >= 2 and clen(cur) >= HEAD_BREAK_MIN)):
            close()
        cur.append(u)
    if cur:
        chunks.append(cur)
    # merge short tails
    merged = []
    for c in chunks:
        if merged and clen(c) < TAIL_MIN and clen(merged[-1]) + clen(c) <= HARD_MAX:
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    if len(merged) > 1 and clen(merged[0]) < TAIL_MIN and clen(merged[0]) + clen(merged[1]) <= HARD_MAX:
        merged[1] = merged[0] + merged[1]
        merged = merged[1:]
    return merged


def overlap_text(prev_core, first_unit):
    if first_unit["table"] or prev_core[-1]["table"]:
        return ""
    sents = sentences(prev_core[-1]["text"])
    pick, tot = [], 0
    for s in reversed(sents):
        if tot + len(s) + (1 if pick else 0) > OVERLAP_MAX:
            break
        pick.insert(0, s)
        tot += len(s) + (1 if len(pick) > 1 else 0)
    ov = " ".join(pick)
    return ov if len(ov) >= OVERLAP_MIN else ""


def path_str(stack):
    titles = [t for _, t in stack]
    if len(titles) > 4:
        titles = [titles[0]] + titles[-3:]
    return " > ".join(titles)


def pool_for(doc_id, top):
    if doc_id == "zurich_impresa":
        return "test_pool"
    held = HELD_OUT[doc_id]
    if doc_id == "zurich_salute":
        return "validation_pool" if top.startswith(held) else "train_pool"
    return "validation_pool" if n(top) == n(held) else "train_pool"


def process(doc_id):
    cfg = CONFIG[doc_id]
    lines = load(doc_id)
    if cfg["mode"] == "ladder":
        lines = mark_ladder(doc_id, lines, cfg)
        synth = {}
        miss = 0
    else:
        dipa = find_dipa_start(lines)
        cfg = dict(cfg)
        cfg["front"] = [(a, b) if a else (dipa, b) for a, b in cfg["front"]]
        # headings of front pages (DIP, DIPA)
        for ln in lines:
            if ln["page"] < cfg["ladder_start"] and ln["kind"] == "text" and ln["bold"] and ln["page"] >= 3 and is_short_title(ln["t"]) \
                    and (ln["size"] >= 10.9 or ln["t"].endswith("?")) and words(ln["t"]) >= 2:
                ln["level"], ln["title"] = 2, ln["t"]
        synth, miss = mark_toc(doc_id, lines, cfg)
    # char offsets
    pos = 0
    for ln in lines:
        ln["cs"] = pos
        pos += len(ln["t"]) + 1
        ln["ce"] = pos - 1
    total_chars = pos
    # walk with heading stack
    stack = []
    sections = collections.OrderedDict()
    front = sorted([(a, b) for a, b in cfg["front"] if a], key=lambda x: x[0])
    heads = []

    def front_label(p):
        lab = None
        for a, b in front:
            if p >= a:
                lab = b
        return lab

    cur_top = None
    for idx, ln in enumerate(lines):
        for lvl, title in synth.get(idx, []):
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            stack.append((lvl, title))
            if lvl == 1:
                cur_top = title
            heads.append((doc_id, ln["page"], lvl, title, "synthetic"))
        p = ln["page"]
        if p < cfg["ladder_start"]:
            lab = front_label(p)
            if cur_top != lab or not stack or stack[0][1] != lab:
                cur_top = lab
                stack = [(1, lab)]
        elif cur_top is None:
            cur_top = "Frontespizio"
            stack = [(1, "Frontespizio")]
        if ln["level"]:
            lvl = ln["level"]
            if p < cfg["ladder_start"] and lvl == 1:
                lvl = 2
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            stack.append((lvl, ln["title"]))
            if lvl == 1:
                cur_top = ln["title"]
            heads.append((doc_id, p, lvl, ln["title"], "line"))
        ln["path"] = path_str(stack)
        ln["top"] = cur_top
        sections.setdefault(cur_top, []).append(ln)
    # build chunks per top section
    meta = META[doc_id]
    all_chunks, excluded_chars, seq = [], 0, collections.Counter()
    for top, items in sections.items():
        if top in DROP_SECTIONS:
            excluded_chars += sum(len(i["t"]) + 1 for i in items)
            continue
        units = make_units(items)
        chs = assemble(units)
        prev_core = None
        for c in chs:
            core = "\n".join(u["text"] for u in c)
            ov = overlap_text(prev_core, c[0]) if prev_core else ""
            text = (ov + "\n" + core) if ov else core
            text = BAD.sub(" ", text)
            page = c[0]["page"]
            seq[page] += 1
            cid = f"{doc_id}_p{page:03d}_c{seq[page]:02d}"
            all_chunks.append({
                "chunk_id": cid, "doc_id": doc_id, "insurer": meta[0], "product": meta[1], "branch": meta[2], "family": doc_id,
                "page": page, "page_end": c[-1]["page"], "section_path": c[0]["path"], "top_section": top,
                "char_start": c[0]["cs"], "char_end": c[-1]["ce"], "n_chars": len(text), "overlap_chars": len(ov),
                "pool": pool_for(doc_id, top), "is_table": all(u["table"] for u in c), "text": text,
                "_core_chars": sum(len(u["text"]) + 1 for u in c)})
            prev_core = c
    return all_chunks, heads, total_chars, excluded_chars, miss, sections


def report(results):
    out = ["# Chunk report (stage 2)\n"]
    rng = random.Random(SEED)
    est = {"zurich_salute": 170, "generali_immagina_adesso": 320, "zurich_impresa": 560}
    for doc_id, (chs, heads, total, excl, miss, sections) in results.items():
        ns = [c["n_chars"] for c in chs]
        iv = sorted((c["char_start"], c["char_end"]) for c in chs)
        core, hi = 0, -1
        for a, b in iv:
            a = max(a, hi)
            if b > a:
                core += b - a
            hi = max(hi, b)
        out.append(f"## {doc_id}\n")
        out.append(f"- chunks: **{len(chs)}** (estimate {est[doc_id]}, difference {100*(len(chs)-est[doc_id])/est[doc_id]:+.0f}%)")
        out.append(f"- chars: min {min(ns)}, median {int(statistics.median(ns))}, max {max(ns)}; under 300: {sum(x < 300 for x in ns)}; over 2400: {sum(x > 2400 for x in ns)}")
        out.append(f"- coverage of extracted text (core, no overlap): {100*core/total:.1f}% (dropped sections {excl} chars = {100*excl/total:.1f}%; kept+dropped = {100*(core+excl)/total:.1f}%)")
        out.append(f"- forbidden characters: {sum(bool(BAD.search(c['text'])) for c in chs)}")
        out.append(f"- headings: {len(heads)} ({sum(h[4]=='synthetic' for h in heads)} synthetic, TOC entries not found on page: {miss})")
        out.append(f"- pools: {dict(collections.Counter(c['pool'] for c in chs))}\n")
        out.append("| top section | pool | chunks | chars |\n| --- | --- | ---: | ---: |")
        byt = collections.OrderedDict()
        for c in chs:
            d = byt.setdefault(c["top_section"], [c["pool"], 0, 0])
            d[1] += 1
            d[2] += c["n_chars"]
        for t, (pl, k, ch) in byt.items():
            out.append(f"| {t[:70]} | {pl} | {k} | {ch} |")
        if doc_id in HELD_OUT:
            hs = [c for c in chs if c["pool"] == "validation_pool"]
            out.append(f"\n**Held-out section** `{HELD_OUT[doc_id]}`: pages {min(c['page'] for c in hs)} to {max(c['page_end'] for c in hs)}, {len(hs)} chunks\n")
        out.append("")
    # samples at the end
    out.append("# 20 random chunks per document\n")
    for doc_id, (chs, *_r) in results.items():
        out.append(f"## {doc_id}\n")
        for c in rng.sample(chs, min(20, len(chs))):
            out.append(f"### {c['chunk_id']} | {c['section_path']} | pool={c['pool']} | {c['n_chars']} chars\n```\n{c['text']}\n```\n")
    (OUT / "chunk_report.md").write_text("\n".join(out), encoding="utf-8")


def main():
    results = {d: process(d) for d in META}
    allc = []
    for d, (chs, heads, *_r) in results.items():
        allc += chs
        with open(OUT / f"headings_{d}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["doc_id", "page", "level", "title", "source"])
            w.writerows(heads)
    ids = [c["chunk_id"] for c in allc]
    assert len(ids) == len(set(ids)), "duplicate chunk ids"
    with open(OUT / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in allc:
            c = {k: v for k, v in c.items() if not k.startswith("_")}
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    report(results)
    for d, (chs, heads, total, excl, miss, _s) in results.items():
        print(d, len(chs), "chunks; heads", len(heads), "toc-miss", miss, "pools", dict(collections.Counter(c["pool"] for c in chs)))


if __name__ == "__main__":
    main()
