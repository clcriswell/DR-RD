import copy
import json
from pathlib import Path
from typing import Any, Callable

import jsonschema
import pytest
from jinja2 import Environment, meta

from dr_rd.prompting import PromptFactory, registry
from dr_rd.prompting.sanitizers import neutralize_project_terms
from dr_rd.evaluators import compartment_check

from core.agents.prompt_agent import PromptFactoryAgent
from core.agents.cto_agent import CTOAgent
from core.agents.finance_agent import FinanceAgent
from core.agents.finance_specialist_agent import FinanceSpecialistAgent
from core.agents.hrm_agent import HRMAgent
from core.agents.ip_analyst_agent import IPAnalystAgent
from core.agents.marketing_agent import MarketingAgent
from core.agents.materials_engineer_agent import MaterialsEngineerAgent
from core.agents.patent_agent import PatentAgent
from core.agents.planner_agent import PlannerAgent
from core.agents.reflection_agent import ReflectionAgent
from core.agents.regulatory_agent import RegulatoryAgent
from core.agents.regulatory_specialist_agent import RegulatorySpecialistAgent
from core.agents.research_scientist_agent import ResearchScientistAgent
from core.agents.synthesizer_agent import SynthesizerAgent
from core.agents.chief_scientist_agent import ChiefScientistAgent
from core.agents.mechanical_systems_lead_agent import MechanicalSystemsLeadAgent
from core.agents.qa_agent import QAAgent


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


def test_planner_schema_rejects_missing_plan_metadata(planner_schema):
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
    plan.pop("plan_id")
    with pytest.raises(jsonschema.ValidationError):
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
    assert "Required top-level JSON keys" in system
    for key in (
        "plan_id",
        "role",
        "task",
        "findings",
        "constraints",
        "assumptions",
        "metrics",
        "next_steps",
        "risks",
        "sources",
    ):
        assert key in system
    assert "Inputs = prerequisites or data the assignee needs" in system
    assert "Outputs = deliverables or decisions produced" in system
    assert "Constraints = guardrails, policies, or limits to respect" in system
    assert "Populate them even when uncertain" in system
    assert (
        "Keep titles, summaries, descriptions, inputs, outputs, and constraints neutral." in system
    )
    assert "Do not reference or hint at the overall project idea in any field." in system
    assert "Replace any idea-specific names with neutral terms like 'the system'." in system


def test_planner_prompt_masks_project_name():
    pf = PromptFactory()
    spec = {
        "role": "Planner",
        "task": "Outline execution phases",
        "inputs": {
            "idea": "ChronoGlide Drone Pro: Rapid-response UAV for mountain rescue",
            "constraints_section": "",
            "risk_section": "",
        },
        "io_schema_ref": "dr_rd/schemas/planner_v1.json",
    }
    prompt = pf.build_prompt(spec)
    user = prompt["user"]
    assert "ChronoGlide" not in user
    assert "Drone Pro" not in user
    assert "the system" in user
    assert "Project idea" in user


def test_neutralize_project_terms_replaces_named_entities():
    text = "Launch the NebulaLink Beacon Series for remote monitoring"
    neutral, replaced = neutralize_project_terms(text)
    assert "NebulaLink" not in neutral
    assert "Beacon Series" not in neutral
    assert neutral.startswith("Launch the system")
    assert any("NebulaLink" in item for item in replaced)


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


def test_reflection_prompt_excludes_project_idea():
    tpl = registry.get("Reflection")
    assert tpl is not None
    template_user = tpl.user_template or ""
    assert "Project Idea" not in template_user
    assert "{{ idea" not in template_user

    pf = PromptFactory()
    task_payload = {
        "summary": "Not determined",
        "findings": "",
        "risks": [],
    }
    spec = {
        "role": "Reflection",
        "task": json.dumps(task_payload),
        "inputs": {
            "task_payload": json.dumps(task_payload),
            "task_description": "Not determined",
            "task_inputs": ["Not determined"],
            "task_outputs": ["Not determined"],
            "task_constraints": ["Not determined"],
            "idea": "NebulaLink Beacon Series",
        },
        "io_schema_ref": "dr_rd/schemas/reflection_v1.json",
    }

    prompt = pf.build_prompt(spec)
    user = prompt["user"]
    assert "Project Idea" not in user
    assert "NebulaLink" not in user
    assert "Existing outputs" in user
    assert "Not determined" in user


PROMPT_AGENT_CASES = [
    (
        "CTO",
        CTOAgent,
        lambda agent, idea, payload: agent.act(idea, payload),
    ),
    (
        "Regulatory",
        RegulatoryAgent,
        lambda agent, idea, payload: agent.act(idea, payload),
    ),
    (
        "Finance",
        FinanceAgent,
        lambda agent, idea, payload: agent.act(idea, payload),
    ),
    (
        "Marketing Analyst",
        MarketingAgent,
        lambda agent, idea, payload: agent.act(idea, payload),
    ),
    (
        "IP Analyst",
        IPAnalystAgent,
        lambda agent, idea, payload: agent.act(idea, payload),
    ),
    (
        "Patent",
        PatentAgent,
        lambda agent, idea, payload: agent.act(idea, payload),
    ),
    (
        "Research Scientist",
        ResearchScientistAgent,
        lambda agent, idea, payload: agent.act(idea, payload),
    ),
    (
        "HRM",
        HRMAgent,
        lambda agent, idea, payload: agent.act(idea, payload),
    ),
    (
        "Materials Engineer",
        MaterialsEngineerAgent,
        lambda agent, idea, payload: agent(payload, meta={"context": idea}),
    ),
]


def _sample_plan_task() -> dict:
    return {
        "id": "T-01",
        "title": "Assess subsystem",
        "summary": "Review the subsystem design",
        "description": "Review subsystem interfaces and document open questions.",
        "role": "Research Scientist",
        "inputs": ["Subsystem interface spec", "Design review notes"],
        "outputs": ["Risk register", "Open questions"],
        "constraints": ["Stay within compliance scope"],
    }


def test_prompt_factory_agents_forward_task_scope(monkeypatch):
    captured: list[dict] = []

    def _capture(self, spec: dict, **kwargs):
        captured.append({"spec": copy.deepcopy(spec), "cls": type(self)})
        return "{}"

    monkeypatch.setattr(PromptFactoryAgent, "run_with_spec", _capture)

    idea = "Confidential concept"
    for role, agent_cls, runner in PROMPT_AGENT_CASES:
        agent = agent_cls("test-model")
        runner(agent, idea, _sample_plan_task())

    assert len(captured) == len(PROMPT_AGENT_CASES)
    for entry in captured:
        spec = entry["spec"]
        inputs = spec.get("inputs", {})
        assert inputs.get("task_description") == "Review subsystem interfaces and document open questions."
        assert inputs.get("task_inputs") == ["Subsystem interface spec", "Design review notes"]
        assert inputs.get("task_outputs") == ["Risk register", "Open questions"]
        assert inputs.get("task_constraints") == ["Stay within compliance scope"]
        assert "idea" not in inputs


def test_scope_hook_integration(monkeypatch):
    captured: list[dict] = []

    def _capture(self, spec: dict, **kwargs):
        captured.append(copy.deepcopy(spec))
        return "{}"

    monkeypatch.setattr(PromptFactoryAgent, "run_with_spec", _capture)
    monkeypatch.setattr("core.agents.planner_agent.preflight", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        "core.agents.planner_agent.feature_flags",
        type("Flags", (), {"POLICY_AWARE_PLANNING": False})(),
        raising=False,
    )

    idea = "Compartmentalized initiative"
    plan_task = _sample_plan_task()
    for _role, agent_cls, runner in PROMPT_AGENT_CASES:
        agent = agent_cls("test-model")
        runner(agent, idea, plan_task)

    synth_payload = {"CTO": {"summary": "ok", "findings": "", "risks": [], "next_steps": [], "sources": []}}
    reflection_payload = {"summary": "Not determined"}
    additional_cases: list[tuple[type, Callable[[Any], None]]] = [
        (PlannerAgent, lambda agent: agent.act(idea, plan_task)),
        (ChiefScientistAgent, lambda agent: agent.act(idea, plan_task)),
        (MechanicalSystemsLeadAgent, lambda agent: agent.act(idea, plan_task)),
        (RegulatorySpecialistAgent, lambda agent: agent.act(idea, plan_task)),
        (SynthesizerAgent, lambda agent: agent.act(idea, synth_payload)),
        (ReflectionAgent, lambda agent: agent.act(idea, reflection_payload)),
    ]

    for agent_cls, invoke in additional_cases:
        agent = agent_cls("test-model")
        invoke(agent)

    assert len(captured) == len(PROMPT_AGENT_CASES) + len(additional_cases)
    for spec in captured:
        hooks = spec.get("evaluation_hooks") or []
        assert "compartment_check" in hooks


def test_integration_contradiction(monkeypatch):
    def fake_run(self, spec: dict, **kwargs):
        payload = {
            "summary": "Base summary",
            "key_points": [],
            "role": "Synthesizer",
            "task": "compose final report",
            "findings": "",
            "risks": [],
            "next_steps": [],
            "sources": [],
            "confidence": 1.0,
        }
        return json.dumps(payload)

    monkeypatch.setattr(PromptFactoryAgent, "run_with_spec", fake_run)

    answers = {
        "CTO": {
            "decision": "Proceed",
            "summary": "Subsystem ready for integration",
            "sources": ["http://example.com/design"],
        },
        "Regulatory": {
            "decision": "Hold",
            "summary": "Subsystem requires additional review",
        },
        "QA": {"summary": "Not determined"},
    }

    agent = SynthesizerAgent("test-model")
    result = agent.act("Idea", answers)
    data = json.loads(result)

    contradictions = data.get("contradictions", [])
    assert any("decision" in msg and "CTO" in msg and "Regulatory" in msg for msg in contradictions)
    assert any("QA" in msg and "Not determined" in msg for msg in contradictions)
    assert data.get("confidence", 1.0) < 1.0


def test_qa_agent_injects_task_scope(monkeypatch):
    captured: dict[str, dict] = {}

    def fake_build(self, spec: dict):
        captured["spec"] = copy.deepcopy(spec)
        return {"system": "", "user": "", "llm_hints": {}, "io_schema_ref": QAAgent.IO_SCHEMA}

    monkeypatch.setattr(PromptFactory, "build_prompt", fake_build)
    monkeypatch.setattr("core.agents.qa_agent.allow_tools", lambda role, tools: None)

    def fake_call_tool(*args, **kwargs):
        return {"ok": True}

    monkeypatch.setattr("core.agents.qa_agent.call_tool", fake_call_tool)

    class DummyResponse:
        def __init__(self, content: str):
            self.content = content

    def fake_complete(*args, **kwargs):
        payload = {
            "role": "QA",
            "task": "",
            "summary": "",
            "findings": "",
            "risks": [],
            "next_steps": [],
            "sources": [],
            "defects": [],
            "coverage": "",
        }
        return DummyResponse(json.dumps(payload))

    monkeypatch.setattr("core.agents.qa_agent.complete", fake_complete)

    agent = QAAgent("test-model")
    task = _sample_plan_task()
    agent.run(task, requirements=[], tests=[], defects=[], idea="Secret", context="Context")

    inputs = captured["spec"]["inputs"]
    assert inputs.get("task_description") == "Review subsystem interfaces and document open questions."
    assert inputs.get("task_inputs") == ["Subsystem interface spec", "Design review notes"]
    assert inputs.get("task_outputs") == ["Risk register", "Open questions"]
    assert inputs.get("task_constraints") == ["Stay within compliance scope"]
    assert "idea" not in inputs
    hooks = captured["spec"].get("evaluation_hooks", [])
    assert "compartment_check" in hooks


def test_finance_specialist_includes_scope_hook(monkeypatch):
    captured: dict[str, dict] = {}

    def fake_build(self, spec: dict):
        captured["spec"] = copy.deepcopy(spec)
        return {
            "system": "",
            "user": "",
            "llm_hints": {},
            "io_schema_ref": FinanceSpecialistAgent.IO_SCHEMA,
        }

    monkeypatch.setattr(PromptFactory, "build_prompt", fake_build)
    monkeypatch.setattr("core.agents.finance_specialist_agent.allow_tools", lambda *_args, **_kwargs: None)

    def fake_call_tool(*_args, **_kwargs):
        return {}

    monkeypatch.setattr("core.agents.finance_specialist_agent.call_tool", fake_call_tool)

    class DummyResponse:
        def __init__(self, content: str):
            self.content = content

    monkeypatch.setattr("core.agents.finance_specialist_agent.complete", lambda *args, **kwargs: DummyResponse("{}"))
    monkeypatch.setattr("core.agents.finance_specialist_agent.validate", lambda *args, **kwargs: None)

    agent = FinanceSpecialistAgent("test-model")
    agent.run("Assess budget", [], [], {"mean": 0, "std": 1})

    hooks = captured["spec"].get("evaluation_hooks", [])
    assert "compartment_check" in hooks


def test_scope_leak_detection():
    ok, reason = compartment_check("Idea: reveal confidential project")
    assert ok is False
    assert reason == "idea_reference"

    cross_scope_payload = {
        "summary": "Coordinate with the CTO and Marketing Analyst on the broader rollout plan.",
        "findings": "All good.",
    }
    ok, reason = compartment_check(cross_scope_payload)
    assert ok is False
    assert reason == "cross_role_reference"

    ok, reason = compartment_check({"analysis": "Focus on the assigned subsystem deliverable only."})
    assert ok is True
    assert reason == ""
