from utils import survey


from utils import survey


def test_all_threes():
    responses = {k: 3 for k in survey.SUS_ITEMS}
    assert survey.score_sus(responses) == 50


def test_all_high():
    responses = {}
    for i, k in enumerate(survey.SUS_ITEMS.keys(), start=1):
        responses[k] = 5 if i % 2 == 1 else 1
    assert survey.score_sus(responses) == 100


def test_all_low():
    responses = {}
    for i, k in enumerate(survey.SUS_ITEMS.keys(), start=1):
        responses[k] = 1 if i % 2 == 1 else 5
    assert survey.score_sus(responses) == 0


def test_normalize_seq():
    assert survey.normalize_seq(0) == 1
    assert survey.normalize_seq(8) == 7
