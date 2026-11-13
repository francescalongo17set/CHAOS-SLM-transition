"""Derive dataset v2 from final/ (v1): the orchestrator no longer routes to `clarification`.

Run: python -I code/make_v2.py
Reads  final/{train,validation,test}/   (v1, never modified)
Writes final_v2/{train,validation,test}/ with:
  - support.expected_route recomputed by the v2 rule (4 routes, no clarification),
  - support.expected_route_v1 kept for traceability,
  - labels.missing_info and support.slot_status/required_slots/filled_slots KEPT as metadata
    (not scored and not trained on in v2, owner decision 13 Nov, option B),
  - query text, context, ids and qa.jsonl untouched.
v2 rule: out_of_scope -> refuse; quick_reply -> quick_reply;
         ibip_screening / client_drafting / complex -> agentic; otherwise lightweight.
A missing slot no longer changes the route.
"""
import hashlib, json, shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, DST = ROOT / "final", ROOT / "final_v2"
SENSITIVE = {"ibip_screening", "client_drafting"}
ROUTES_V2 = ("lightweight", "agentic", "refuse", "quick_reply")


def route_v2(scope, feature, complexity):
    if scope == "out_of_scope":
        return "refuse"
    if scope == "quick_reply":
        return "quick_reply"
    if feature in SENSITIVE or complexity == "complex":
        return "agentic"
    return "lightweight"


def main():
    if DST.exists():
        shutil.rmtree(DST)
    for sp in ("train", "validation", "test"):
        (DST / sp).mkdir(parents=True)
        rows = [json.loads(l) for l in open(SRC / sp / "router.jsonl", encoding="utf-8") if l.strip()]
        moved = Counter()
        for r in rows:
            lab, sup = r["labels"], r["support"]
            old = sup["expected_route"]
            new = route_v2(lab["scope_check"], lab["feature"], lab.get("complexity"))
            # only the clarification rows may move; every other v1 route must be unchanged
            assert (old == "clarification") or old == new, (r["query_id"], old, new)
            assert new in ROUTES_V2
            sup["expected_route_v1"] = old
            sup["expected_route"] = new
            if old == "clarification":
                moved[new] += 1
        with open(DST / sp / "router.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        shutil.copy(SRC / sp / "qa.jsonl", DST / sp / "qa.jsonl")
        man = json.load(open(SRC / sp / "manifest.json", encoding="utf-8"))
        man["dataset_version"] = "v2"
        man["derived_from"] = {"dir": "final", "router_sha256": hashlib.sha256(
            (SRC / sp / "router.jsonl").read_bytes()).hexdigest()}
        man["router_route_balance"] = dict(Counter(r["support"]["expected_route"] for r in rows))
        man["v2_clarification_rows_moved"] = dict(moved)
        man["files"] = {k: v for k, v in man.get("files", {}).items()}
        for name in ("router.jsonl", "qa.jsonl"):
            if name in man["files"]:
                man["files"][name] = hashlib.sha256((DST / sp / name).read_bytes()).hexdigest()
        json.dump(man, open(DST / sp / "manifest.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(sp, len(rows), man["router_route_balance"], "moved:", dict(moved))
    (DST / "README.md").write_text(
        "# Dataset v2 (derived from final/)\n\nSame rows and text as v1. Only `support.expected_route` changed: "
        "the `clarification` route is gone (the agent gathers missing information itself).\n\n"
        "- v2 rule: out_of_scope -> refuse; quick_reply -> quick_reply; IBIP, client drafting or complex -> agentic; otherwise lightweight.\n"
        "- The 508 v1 clarification rows move to `agentic` (414, sensitive or complex) or `lightweight` (94, simple and not sensitive).\n"
        "- `labels.missing_info`, `support.slot_status`, `required_slots`, `filled_slots` and `support.expected_route_v1` are kept as metadata. "
        "They are not scored and not used for training in v2.\n"
        "- Rebuild with `python -I code/make_v2.py`.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
