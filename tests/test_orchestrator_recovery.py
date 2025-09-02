import pytest
from pydantic import ValidationError

from core.orchestrator import _normalize_plan_payload
from core.schemas import Plan


def test_orchestrator_recovery_normalizes_and_validates():
    data = {"tasks": [{"role": "CTO", "objective": "Assess"}]}
    with pytest.raises(ValidationError):
        Plan.model_validate(data)
    norm = _normalize_plan_payload(data)
    plan = Plan.model_validate(norm)
    assert plan.tasks[0].title == "CTO"
    assert plan.tasks[0].summary == "Assess"
