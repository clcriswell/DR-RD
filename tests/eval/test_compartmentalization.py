import json
from pathlib import Path

import jsonschema
import pytest

from dr_rd.prompting import registry


@pytest.fixture(scope="module")
def planner_schema():
    schema_path = Path("dr_rd/schemas/planner_v1.json")
    return json.loads(schema_path.read_text())


def test_planner_schema_requires_extended_task_fields(planner_schema):
    plan = {
        "plan_id": "plan-001",
        "tasks": [
            {
                "id": "T01",
                "title": "Scoping",
                "summary": "Scope technical work",
                "description": "Outline architecture milestones.",
                "role": "CTO",
                "inputs": ["Not determined"],
                "outputs": ["Architecture outline"],
                "constraints": ["Budget cap"],
            }
        ],
        "constraints": "Budget cap",
        "assumptions": "",
        "metrics": "",
        "next_steps": "Continue",
        "role": "Planner",
        "task": "Organize",
        "findings": "Neutral summary",
        "risks": ["Timeline"],
        "sources": ["Internal"],
    }
    jsonschema.validate(plan, planner_schema)


def test_planner_schema_rejects_missing_extended_fields(planner_schema):
    plan = {
        "plan_id": "plan-001",
        "tasks": [
            {
                "id": "T01",
                "title": "Scoping",
                "summary": "Scope technical work",
                "description": "Outline architecture milestones.",
                "role": "CTO",
                "outputs": ["Architecture outline"],
                "constraints": ["Budget cap"],
            }
        ],
        "constraints": "Budget cap",
        "assumptions": "",
        "metrics": "",
        "next_steps": "Continue",
        "role": "Planner",
        "task": "Organize",
        "findings": "Neutral summary",
        "risks": ["Timeline"],
        "sources": ["Internal"],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(plan, planner_schema)


def test_planner_prompt_instructs_compartmentalized_fields():
    tpl = registry.get("Planner")
    assert tpl is not None
    system = tpl.system
    assert "inputs" in system
    assert "outputs" in system
    assert "constraints" in system
    assert "Do not reference the overall idea" in system
    assert "Keep task descriptions neutral" in system
    assert '"constraints": []' in system
