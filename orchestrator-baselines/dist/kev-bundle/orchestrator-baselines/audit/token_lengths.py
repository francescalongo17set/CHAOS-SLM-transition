"""Audit item 6: token length of the serialized state (reference tokenizer).
Run from orchestrator-baselines/ with the common/ venv: python -m audit.token_lengths"""
import json
import statistics
from pathlib import Path

from common import data
from common.state import serialize_state
from common.tokens import RefTokenizer, REF_TOKENIZER_ID, REF_TOKENIZER_REVISION

tok = RefTokenizer()
out = {"_tokenizer": f"{REF_TOKENIZER_ID}@{REF_TOKENIZER_REVISION}"}
for split in data.SPLITS:
    n = sorted(tok.count_state(serialize_state(r.model_input)) for r in data.load_split(split))
    out[split] = {"min": n[0], "median": int(statistics.median(n)), "p95": n[int(0.95 * (len(n) - 1))],
                  "max": n[-1], "gt512": sum(x > 512 for x in n), "gt768": sum(x > 768 for x in n),
                  "gt1024": sum(x > 1024 for x in n)}
p = Path(__file__).parent / "token_lengths.json"
p.write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
