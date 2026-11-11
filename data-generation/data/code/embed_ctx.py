"""Stage 6 variant of stage 4a: embed 'section_path + newline + text' (contextualised chunks). Keys e5ctx, bgectx."""
import json, sys, time
from pathlib import Path
import numpy as np, torch
from sentence_transformers import SentenceTransformer
ROOT = Path(__file__).resolve().parent.parent; IDX = ROOT / "index"
MODELS = {"e5ctx": ("intfloat/multilingual-e5-base", "passage: ", 512), "bgectx": ("BAAI/bge-m3", "", 1024)}
chunks = [json.loads(l) for l in open(ROOT / "chunks/chunks.jsonl", encoding="utf-8")]
dev = "mps" if torch.backends.mps.is_available() else "cpu"
def doc(c): return f"{c['product']} - {c['section_path']}\n{c['text']}"
for key in sys.argv[1:] or MODELS:
    name, prefix, maxlen = MODELS[key]; t = time.time()
    m = SentenceTransformer(name, device=dev); m.max_seq_length = maxlen
    texts = [prefix + doc(c) for c in chunks]; order = np.argsort([len(x) for x in texts])
    emb = m.encode([texts[i] for i in order], batch_size=16, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True)
    out = np.zeros_like(emb); out[order] = emb
    np.save(IDX / f"emb_{key}.npy", out.astype(np.float32))
    print(key, out.shape, dev, round(time.time() - t), "s", flush=True)
