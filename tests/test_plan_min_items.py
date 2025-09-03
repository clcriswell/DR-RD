import pytest
from pydantic import ValidationError
from core.schemas import Plan
from core.orchestrator import _coerce_and_fill


def test_plan_requires_tasks():
    with pytest.raises(ValidationError):
        Plan.model_validate({"tasks": []})


def test_normalizer_injects_ids():
    data = {"tasks": [{"role": "Research Scientist", "title": "A", "summary": "B"}]}
    norm = _coerce_and_fill(data)
    validated = Plan.model_validate(norm)
    assert validated.tasks[0].id == "T01"
