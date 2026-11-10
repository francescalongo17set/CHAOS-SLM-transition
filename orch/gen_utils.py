"""Small helpers for synthetic query generation (kept out of the GPU script so CI can test them)."""
import json
import re
import unicodedata


def parse_queries(text: str) -> list:
    """Pull a list of query strings out of a model reply, tolerating code fences and chatter around the JSON."""
    m = re.search(r"\{.*\}|\[.*\]", text, re.S)
    if not m:
        return []
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    items = obj.get("queries", []) if isinstance(obj, dict) else obj
    return [q.strip() for q in items if isinstance(q, str)]


def norm(q: str) -> str:
    q = unicodedata.normalize("NFKD", q.lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(c for c in q if not unicodedata.combining(c))).strip()


def valid(q: str) -> bool:
    n = len(q.split())
    # also drops anything that leaks the recipe ("the passage") and the line separators Kev-style tools choke on
    return 4 <= n <= 70 and not re.search(r"passage|passaggio|articolo fornito| | ", q, re.I)


def dedupe(rows, key="query"):
    seen, out = set(), []
    for r in rows:
        k = norm(r[key])
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def hf_revision(model_id: str) -> str:
    """Hub commit hash of the model (pins the exact weights in the generation report). Needs internet; 'unknown' if offline."""
    try:
        from huggingface_hub import HfApi
        return HfApi().model_info(model_id).sha
    except Exception:
        return "unknown"
