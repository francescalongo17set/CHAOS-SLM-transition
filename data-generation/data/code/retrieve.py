"""Stage 4b: retrieve(question, doc_id, k=5) -> evidence record (book stage 4).

Model, prefixes and settings come from index/retrieval_config.json (frozen at stage 6).
Exact cosine (dot product of normalised vectors), doc_id filter, ties broken by chunk order.
"""
import json, os, sys
import urllib.request, urllib.error
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
IDX = ROOT / "index"
_cache = {}
PORT = int(os.environ.get("RETRIEVE_PORT", "8765"))


def _remote(question, doc_id, k, key):
    """Ask the shared retrieval server (code/retrieval_server.py) so the model is loaded once, not per process."""
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/retrieve", method="POST", headers={"Content-Type": "application/json"},
                                 data=json.dumps({"question": question, "doc_id": doc_id, "k": k, "model": key}).encode())
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def _load(key):
    if key not in _cache:
        from sentence_transformers import SentenceTransformer
        cfg = json.load(open(IDX / "retrieval_config.json"))["models"][key]
        chunks = [json.loads(l) for l in open(ROOT / "chunks/chunks.jsonl", encoding="utf-8")]
        emb = np.load(IDX / f"emb_{key}.npy")
        model = SentenceTransformer(cfg["model"], revision=cfg.get("revision"))
        model.max_seq_length = cfg["max_seq_length"]
        _cache[key] = (cfg, chunks, emb, model, np.array([c["doc_id"] for c in chunks]))
    return _cache[key]


def retrieve(question, doc_id, k=5, model=None):
    key = model or json.load(open(IDX / "retrieval_config.json"))["active"]
    if not os.environ.get("RETRIEVE_NO_SERVER"):
        try:
            return _remote(question, doc_id, k, key)
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if os.environ.get("RETRIEVE_SERVER_ONLY"):
                raise RuntimeError("retrieval server not running: start it with  python -I code/retrieval_server.py")
            print("retrieve: server not found, loading the model in this process (several GB of RAM)", file=sys.stderr)
    cfg, chunks, emb, m, docs = _load(key)
    q = m.encode([cfg["query_prefix"] + question], normalize_embeddings=True, convert_to_numpy=True)[0]
    scores = emb @ q
    idx = np.where(docs == doc_id)[0]
    order = idx[np.lexsort((idx, -np.round(scores[idx], 6)))][:k]
    return [{"rank": r + 1, "score": round(float(scores[i]), 4), "chunk_id": chunks[i]["chunk_id"], "doc_id": chunks[i]["doc_id"],
             "page": chunks[i]["page"], "section_path": chunks[i]["section_path"], "text": chunks[i]["text"]} for r, i in enumerate(order)]
