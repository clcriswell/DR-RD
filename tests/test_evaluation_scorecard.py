import config.feature_flags as ff
from dr_rd.evaluation.scorecard import evaluate


def test_evaluate_disabled(monkeypatch):
    monkeypatch.setattr(ff, "EVALUATORS_ENABLED", False)
    sc = evaluate("text", {})
    assert sc.overall == 1.0
    assert sc.scores == {}


def test_evaluate_enabled_no_llm(monkeypatch):
    monkeypatch.setattr(ff, "EVALUATORS_ENABLED", True)
    sc = evaluate("hello", {})
    assert 0.0 <= sc.overall <= 1.0
