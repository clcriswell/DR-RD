import pytest
from pydantic import ValidationError

from core.schemas import Plan
from core.orchestrator import _normalize_plan_payload


def test_zero_tasks_invalid():
    with pytest.raises(ValidationError):
        Plan.model_validate({"tasks": []})


def test_missing_ids_injected():
    data = {"tasks": [{"role": "Research Scientist", "title": "A", "summary": "B"}]}
    norm = _normalize_plan_payload(data)
    validated = Plan.model_validate(norm)
    assert validated.tasks[0].id == "T01"


def test_legacy_task_field_backfilled():
    data = {"tasks": [{"role": "Engineer", "task": "Build prototype"}]}
    norm = _normalize_plan_payload(data)
    validated = Plan.model_validate(norm)
    t = validated.tasks[0]
    assert t.title == "Build prototype"
    assert t.summary == "Build prototype"
