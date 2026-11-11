"""Stage 4a: embed every chunk with both candidate models (book stage 4)."""
import json, sys, time
from pathlib import Path
import numpy as np, torch
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
IDX = ROOT / "index"; IDX.mkdir(exist_ok=True)
MODELS = {"e5": ("intfloat/multilingual-e5-base", "passage: ", 512), "bge": ("BAAI/bge-m3", "", 1024)}
chunks = [json.loads(l) for l in open(ROOT / "chunks/chunks.jsonl", encoding="utf-8")]
json.dump([c["chunk_id"] for c in chunks], open(IDX / "chunk_order.json", "w"))
dev = "mps" if torch.backends.mps.is_available() else "cpu"
for key in sys.argv[1:] or MODELS:
    name, prefix, maxlen = MODELS[key]
    t = time.time()
    m = SentenceTransformer(name, device=dev)
    m.max_seq_length = maxlen
    texts = [prefix + c["text"] for c in chunks]
    order = np.argsort([len(x) for x in texts])  # batch similar lengths, restore order after
    emb = m.encode([texts[i] for i in order], batch_size=16, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True)
    out = np.zeros_like(emb); out[order] = emb
    np.save(IDX / f"emb_{key}.npy", out.astype(np.float32))
    rev = getattr(m[0].auto_model.config, "_commit_hash", None)
    json.dump({"model": name, "revision": rev, "dim": int(out.shape[1]), "device": dev, "max_seq_length": maxlen, "seconds": round(time.time() - t)},
              open(IDX / f"emb_{key}.json", "w"))
    print(key, out.shape, dev, round(time.time() - t), "s", flush=True)
