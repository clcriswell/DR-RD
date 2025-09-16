import json
from pathlib import Path

import jsonschema
import pytest
from jinja2 import Environment, meta

from dr_rd.prompting import PromptFactory, registry


ISOLATED_AGENT_ROLES = [
    "CTO",
    "Regulatory",
    "Finance",
    "Marketing Analyst",
    "IP Analyst",
    "Patent",
    "Research Scientist",
    "HRM",
    "Materials Engineer",
    "Dynamic Specialist",
    "QA",
]


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
    assert (
        "Each task MUST contain the fields id, title, summary, description, role, inputs, outputs, and constraints." in system
    )
    assert "Inputs = prerequisites or data the assignee needs" in system
    assert "Outputs = deliverables or decisions produced" in system
    assert "Constraints = guardrails, policies, or limits to respect" in system
    assert "Populate them even when uncertain" in system
    assert (
        "Keep titles, summaries, descriptions, inputs, outputs, and constraints neutral." in system
    )
    assert "Do not reference or hint at the overall project idea in any field." in system


def _placeholders_for_template(template: str) -> set[str]:
    env = Environment()
    return meta.find_undeclared_variables(env.parse(template or ""))


def test_agent_prompt_templates_isolate_context():
    for role in ISOLATED_AGENT_ROLES:
        tpl = registry.get(role)
        assert tpl is not None
        assert "Idea:" not in tpl.system
        assert "Idea:" not in (tpl.user_template or "")
        placeholders = _placeholders_for_template(tpl.user_template or "")
        assert placeholders == {
            "task_description",
            "task_inputs",
            "task_outputs",
            "task_constraints",
        }


def test_prompt_factory_renders_isolated_task_context():
    pf = PromptFactory()
    spec = {
        "role": "CTO",
        "task": "Design the control firmware",
        "inputs": {
            "task_description": "Design the control firmware",
            "task_inputs": [
                "Existing electronics specification",
                "Safety requirements",
            ],
            "task_outputs": ["Firmware architecture outline"],
            "task_constraints": ["Meet IEC 62304"],
        },
        "io_schema_ref": "dr_rd/schemas/cto_v2.json",
    }
    prompt = pf.build_prompt(spec)
    user = prompt["user"]
    assert "Idea:" not in user
    assert "Design the control firmware" in user
    assert "Existing electronics specification" in user
    assert "Firmware architecture outline" in user
    assert "Meet IEC 62304" in user
