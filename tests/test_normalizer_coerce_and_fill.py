from pathlib import Path

import pytest

from core.orchestrator import _coerce_and_fill
from core.schemas import Plan


def test_normalizer_coerce_and_fill_basic():
    data = {"tasks": [{"id": "1", "title": "Foo ", "summary": "Bar"}]}
    norm = _coerce_and_fill(data)
    task = norm["tasks"][0]
    assert task["title"] == "Foo"
    assert task["summary"] == "Bar"
    assert task["description"] == "Bar"
    assert task["role"] == "Dynamic Specialist"


def test_normalizer_array_root_wrapped():
    arr = [{"id": "1", "title": "A", "summary": "B", "description": "B"}]
    norm = _coerce_and_fill(arr)
    Plan.model_validate(norm, strict=True)


def test_normalizer_zero_failfast(tmp_path):
    # Ensure debug directory clean
    log_dir = Path("debug/logs")
    if log_dir.exists():
        for p in log_dir.glob("planner_payload_*.json"):
            p.unlink()

    with pytest.raises(ValueError) as exc:
        _coerce_and_fill({"tasks": [{"id": "1", "title": " ", "summary": ""}]})
    assert str(exc.value) == "planner.normalization_zero"
    assert list(log_dir.glob("planner_payload_*.json"))


def test_normalizer_tot_task_field_fallback():
    data = {
        "tasks": [
            {"role": "AI R&D Coordinator", "task": "Clarify requirements with stakeholders"}
        ]
    }

    norm = _coerce_and_fill(data)
    assert norm["_raw_count"] == 1
    assert len(norm["tasks"]) == 1

    task = norm["tasks"][0]
    assert task["id"] == "T01"
    assert task["title"] == "Clarify requirements with stakeholders"
    assert task["summary"] == "Clarify requirements with stakeholders"
    assert task["description"] == "Clarify requirements with stakeholders"

    Plan.model_validate(norm, strict=True)

