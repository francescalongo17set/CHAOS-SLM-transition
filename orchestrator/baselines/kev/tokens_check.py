"""P1 step 4: what does the packed length (`len(enc["ids"])`, the number the API reports as usage.input_tokens)
count? Runs one row with 1 and with 4 questions and prints/saves both. Finding goes into run.json.notes by hand.

  python kev/tokens_check.py --out runs/kev/<run_id>-smoke/tokens_check.json
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.append(str(HERE.parent))

from orchestrator.baselines.kev.adapter import build_request          # noqa: E402
from orchestrator.baselines.common import data                    # noqa: E402
from orchestrator.baselines.common.questions import QuestionConfig   # noqa: E402
from orchestrator.baselines.common.state import serialize_state   # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="jaredpalmer/kev-0.8b@v1.0")
    ap.add_argument("--dtype", default="fp32", choices=["fp32", "bf16"])
    ap.add_argument("--shard", action="store_true", help="split the bf16 backbone over all GPUs (kev/shard.py)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import torch
    from kev.api import to_record
    from kev.checkpoint import Checkpoint, LoadOptions
    from kev.model import admit

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if a.shard:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from orchestrator.baselines.kev.shard import load_sharded
        tok, model = load_sharded(Checkpoint(a.model))
    else:
        tok, model = Checkpoint(a.model).load(device, LoadOptions() if a.dtype == "fp32" else LoadOptions(dtype=torch.bfloat16))
    q = QuestionConfig()
    row = data.load_split("validation")[0]
    state = serialize_state(row.model_input)
    qs = [q.scope_check(), q.feature_classification(), q.complexity_estimation()]
    res = {}
    for n in (1, 2, 3):
        rec, _ = to_record(build_request(state, qs[:n]))
        enc = admit(model, tok, rec)
        res[f"{n}_questions"] = {"len_ids": len(enc["ids"]), "state_tokens": enc["state_tokens"]}
    res["note"] = ("len_ids grows with each extra question by that question's own tokens while state_tokens stays "
                   "fixed => len_ids = state once + all question rows.")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
