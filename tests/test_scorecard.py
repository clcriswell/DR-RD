import pytest

from evaluation import Scorecard
from extensions.abcs import BaseEvaluator


class EvalA(BaseEvaluator):
    def evaluate(self, state):
        return {"score": 0.2, "notes": []}


class EvalB(BaseEvaluator):
    def evaluate(self, state):
        return {"score": 0.8, "notes": []}


def test_scorecard_aggregation():
    weights = {"a": 0.6, "b": 0.4}
    results = {"a": EvalA().evaluate({}), "b": EvalB().evaluate({})}
    sc = Scorecard(weights).aggregate(results)
    assert sc["overall"] == pytest.approx(0.44)
    assert set(sc["metrics"].keys()) == {"a", "b"}
