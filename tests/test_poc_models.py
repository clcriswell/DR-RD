import pytest
from pydantic import ValidationError
from core.poc.testplan import Metric, TestCase, TestPlan


def test_metric_operator_valid():
    m = Metric(name="a", target=1.0, operator=">=")
    assert m.operator == ">="


def test_metric_operator_invalid():
    with pytest.raises(ValidationError):
        Metric(name="a", target=1.0, operator="!=")


def test_testplan_schema():
    tp = TestPlan(project_id="p1", hypothesis="h", tests=[TestCase(id="t1", title="T")])
    assert tp.project_id == "p1"
