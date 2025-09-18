import pytest
from pydantic import ValidationError

from core.schemas import Plan
from core.orchestrator import _coerce_and_fill


def test_zero_tasks_invalid():
    with pytest.raises(ValidationError):
        Plan.model_validate({"tasks": []})


def test_missing_ids_injected():
    data = {"tasks": [{"role": "Research Scientist", "title": "A", "summary": "B"}]}
    norm = _coerce_and_fill(data)
    validated = Plan.model_validate(norm)
    assert validated.tasks[0].id == "T01"


def test_legacy_task_field_backfilled():
    data = {"tasks": [{"role": "Engineer", "task": "Build prototype"}]}
    norm = _coerce_and_fill(data)
    validated = Plan.model_validate(norm)
    t = validated.tasks[0]
    assert t.title == "Build prototype"
    assert t.summary == "Build prototype"


def test_task_inputs_outputs_constraints_lists():
    data = {
        "tasks": [
            {
                "id": "custom-id",
                "role": "CTO",
                "title": "Plan",
                "summary": "Review",
                "description": "Assess",
                "inputs": ["spec", "budget"],
                "outputs": ["report"],
                "constraints": ["48 hours"],
            }
        ]
    }
    norm = _coerce_and_fill(data)
    validated = Plan.model_validate(norm, strict=True)
    task = validated.tasks[0]
    assert task.inputs == ["spec", "budget"]
    assert task.outputs == ["report"]
    assert task.constraints == ["48 hours"]


def test_task_inputs_accepts_mapping():
    data = {
        "tasks": [
            {
                "id": "T9",
                "role": "Finance",
                "title": "Budget",
                "summary": "Summarize",
                "description": "Summarize",
                "inputs": {"sheet": "abc"},
            }
        ]
    }
    norm = _coerce_and_fill(data)
    validated = Plan.model_validate(norm, strict=True)
    task = validated.tasks[0]
    assert task.inputs == {"sheet": "abc"}
    assert task.outputs == []
    assert task.constraints == []
