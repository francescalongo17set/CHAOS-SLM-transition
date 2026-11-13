"""FT-P0 step 4: group-disjoint, route-stratified calibration partition (FT-C-07).

Groups = connected components of rows linked by `bundle_id` or `pair_id` (union-find), so no group straddles."""
import random
from collections import Counter

FRACTION = 0.10
TOLERANCE = 0.20            # per-route calibration count within 20% of fraction * route total (chapter 02)


def groups(rows):
    parent = {r.query_id: r.query_id for r in rows}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    for key in ("bundle_id", "pair_id"):
        first = {}
        for r in rows:
            k = r.support.get("bundle_id") if key == "bundle_id" else r.pair_id
            if k is None:
                continue
            if k in first:
                union(r.query_id, first[k])
            else:
                first[k] = r.query_id
    out = {}
    for r in rows:
        out.setdefault(find(r.query_id), []).append(r)
    return list(out.values())


def route_counts(rows):
    return dict(sorted(Counter(r.support["expected_route"] for r in rows).items()))


def calibration_split(rows, seed, fraction=FRACTION, tolerance=TOLERANCE):
    """-> (train_ids, calibration_ids), both in original file order. Raises if no split meets the per-route tolerance."""
    total = route_counts(rows)
    target = {k: v * fraction for k, v in total.items()}
    hi = {k: int(t * (1 + tolerance)) for k, t in target.items()}
    lo = {k: t * (1 - tolerance) for k, t in target.items()}
    gs = groups(rows)
    for attempt in range(200):                            # deterministic: seed + attempt
        rng = random.Random(f"{seed}:{attempt}")
        order = gs[:]
        rng.shuffle(order)
        got = Counter()
        chosen = []
        for g in order:
            gc = Counter(r.support["expected_route"] for r in g)
            if all(got[k] + gc[k] <= hi[k] for k in gc):
                got.update(gc)
                chosen.append(g)
            if all(got[k] >= lo[k] for k in total):
                break
        if all(lo[k] <= got[k] <= hi[k] for k in total):
            calib = {r.query_id for g in chosen for r in g}
            return ([r.query_id for r in rows if r.query_id not in calib],
                    [r.query_id for r in rows if r.query_id in calib])
    raise RuntimeError("no group-disjoint stratified split within tolerance: stop and ask the owner")
