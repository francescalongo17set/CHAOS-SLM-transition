"""FT-P0 step 5: leakage assertions and counts versus data/manifest.json. Any failure raises AssertionError."""
import json
from pathlib import Path

from split import route_counts, FRACTION, TOLERANCE


def check_partitions(parts, test_ids):
    """parts: {"train","calibration","development"} -> list[Row]."""
    ids = {k: [r.query_id for r in v] for k, v in parts.items()}
    seen = {}
    for k, v in ids.items():
        assert len(v) == len(set(v)), f"duplicate query_id inside {k}"
        for i in v:
            assert i not in seen, f"query_id {i} in both {seen[i]} and {k}"
            seen[i] = k
    assert not (set(seen) & set(test_ids)), "test rows in a training file"
    for key in ("bundle_id", "pair_id"):
        side = {}
        for k in ("train", "calibration"):
            for r in parts[k]:
                g = r.support.get("bundle_id") if key == "bundle_id" else r.pair_id
                if g is None:
                    continue
                assert side.setdefault(g, k) == k, f"{key} {g} straddles train and calibration"
    tr, ca = route_counts(parts["train"] + parts["calibration"]), route_counts(parts["calibration"])
    for route, n in tr.items():
        t = n * FRACTION
        assert abs(ca.get(route, 0) - t) <= t * TOLERANCE + 1e-9, f"calibration {route}: {ca.get(route, 0)} vs target {t:.1f}"


def check_manifest(data_dir):
    """Counts and sha256 of every written file equal the committed manifest."""
    import hashlib
    d = Path(data_dir)
    m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    for rel, info in m["files"].items():
        p = d / rel
        assert hashlib.sha256(p.read_bytes()).hexdigest() == info["sha256"], f"{rel}: hash differs from manifest"
        assert sum(1 for _ in open(p, encoding="utf-8")) == info["rows"], f"{rel}: row count differs"
