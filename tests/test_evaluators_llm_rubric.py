import math

import pytest

import evaluation.llm_rubric as lr
from evaluators.feasibility import FeasibilityEvaluator
from evaluators.novelty import NoveltyEvaluator
from evaluators.compliance import ComplianceEvaluator
from evaluators.cost import CostEvaluator


class FakeWorkspace:
    def __init__(self, text: str):
        self._text = text

    def joined_results_text(self) -> str:
        return self._text

    @property
    def results(self):
        return [self._text]


def test_feasibility_uses_llm_rubric(monkeypatch):
    monkeypatch.setattr(lr, "score_with_rubric", lambda text, rubric: 0.33)
    s = FeasibilityEvaluator().evaluate(FakeWorkspace("feasibility text"))
    assert isinstance(s, float)
    assert math.isclose(s, 0.33, rel_tol=1e-9)


def test_novelty_uses_llm_rubric(monkeypatch):
    monkeypatch.setattr(lr, "score_with_rubric", lambda text, rubric: 0.91)
    s = NoveltyEvaluator().evaluate(FakeWorkspace("novelty text"))
    assert math.isclose(s, 0.91, rel_tol=1e-9)


def test_compliance_uses_llm_rubric(monkeypatch):
    monkeypatch.setattr(lr, "score_with_rubric", lambda text, rubric: 0.72)
    s = ComplianceEvaluator().evaluate(FakeWorkspace("compliance text"))
    assert math.isclose(s, 0.72, rel_tol=1e-9)


def test_cost_numeric_uses_one_minus_cost(monkeypatch):
    def _should_not_be_called(*args, **kwargs):
        raise AssertionError("LLM was called but should not be for numeric cost.")

    monkeypatch.setattr(lr, "score_with_rubric", _should_not_be_called)
    s = CostEvaluator().evaluate(FakeWorkspace("Estimated cost: 0.2"))
    assert math.isclose(s, 0.8, rel_tol=1e-9)


def test_cost_percentage_is_normalized(monkeypatch):
    def _should_not_be_called(*args, **kwargs):
        raise AssertionError("LLM was called but should not be for percentage cost.")

    monkeypatch.setattr(lr, "score_with_rubric", _should_not_be_called)
    s = CostEvaluator().evaluate(FakeWorkspace("Projected budget: 25% of allocation"))
    assert math.isclose(s, 0.75, rel_tol=1e-9)


def test_cost_tbd_falls_back_to_llm(monkeypatch):
    monkeypatch.setattr(lr, "score_with_rubric", lambda text, rubric: 0.4)
    s = CostEvaluator().evaluate(FakeWorkspace("Costs TBD; scope under refinement."))
    assert math.isclose(s, 0.4, rel_tol=1e-9)

