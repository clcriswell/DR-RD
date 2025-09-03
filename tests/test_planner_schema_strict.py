import pytest
from pydantic import ValidationError

from core.orchestrator import _coerce_and_fill
from core.schemas import Plan


def test_planner_schema_strict_rejects_bad_keys():
    data = {"tasks": [{"foo": "bar"}]}
    with pytest.raises(ValidationError):
        Plan.model_validate(data)
    norm = _coerce_and_fill(data)
    with pytest.raises(ValidationError):
        Plan.model_validate(norm)
