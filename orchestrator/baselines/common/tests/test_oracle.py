"""Mandatory dispatcher oracle (chapter 04): gold fields -> route == support.expected_route,
on every row of train, validation and test. Any mismatch is reported with query_ids."""
from orchestrator.baselines.common import data
import pytest

from orchestrator.baselines.common import dispatcher


@pytest.mark.parametrize("split", data.SPLITS)
def test_oracle(split):
    rows = data.load_split(split)
    bad = [(r.query_id, dispatcher.gold_record(r), r.support["expected_route"])
           for r in rows if dispatcher.dispatch_gold(r) != r.support["expected_route"]]
    assert not bad, f"{len(bad)} oracle mismatches in {split}: {bad[:20]}"
