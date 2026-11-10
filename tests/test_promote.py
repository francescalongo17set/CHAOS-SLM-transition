from scripts.ci_register import better

CHAMP = {"test_safety_recall": 0.90, "gold_safety_recall": 0.93, "test_acc_route": 0.93, "gold_acc_route": 0.94}


def m(**kw):
    return {**CHAMP, **kw}


def test_promotes_when_more_accurate_and_safety_holds():
    assert better(m(test_acc_route=0.95), CHAMP)


def test_equal_model_is_not_promoted():
    assert not better(dict(CHAMP), CHAMP)


def test_safety_regression_blocks_promotion_even_if_more_accurate():
    assert not better(m(test_acc_route=0.99, gold_safety_recall=0.90), CHAMP)


def test_less_accurate_is_not_promoted():
    assert not better(m(gold_acc_route=0.90), CHAMP)
