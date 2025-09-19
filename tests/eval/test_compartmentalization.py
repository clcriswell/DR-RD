import copy
import json
from pathlib import Path
from typing import Any, Callable

import jsonschema
import pytest
from jinja2 import Environment, meta

from dr_rd.prompting import PromptFactory, registry
from dr_rd.prompting.planner_specificity import task_contains_concrete_detail
from dr_rd.prompting.sanitizers import neutralize_project_terms
from dr_rd.evaluators import compartment_check

from config import feature_flags
from core.agents.prompt_agent import PromptFactoryAgent, prepare_prompt_inputs
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


def test_planner_schema_complete(monkeypatch, planner_schema):
    payload = {
        "tasks": [
            {
                "id": "T01",
                "title": "Scoping",
                "summary": "Scope technical work",
                "description": "Outline architecture milestones.",
                "role": "CTO",
                "inputs": ["Design brief"],
                "outputs": ["Architecture outline"],
                "constraints": ["Budget cap"],
            }
        ]
    }

    class DummyResult:
        def __init__(self, text: str) -> None:
            self.content = text
            self.raw = {}

    call_counter = {"count": 0}

    def fake_complete(system_prompt: str, user_prompt: str, **kwargs: Any) -> DummyResult:
        call_counter["count"] += 1
        return DummyResult(json.dumps(payload))

    monkeypatch.setattr("core.agents.base_agent.complete", fake_complete)
    monkeypatch.setattr(feature_flags, "POLICY_AWARE_PLANNING", False)
    monkeypatch.setattr(feature_flags, "SAFETY_ENABLED", False)
    monkeypatch.setattr(feature_flags, "FILTERS_STRICT_MODE", False)

    agent = PlannerAgent("Planner", "test-model")
    result = agent.act("Nebula concept", "Outline execution phases")
    plan = json.loads(result)

    assert call_counter["count"] == 1
    assert isinstance(plan, dict)
    for key in planner_schema["properties"].keys():
        assert key in plan

    assert isinstance(plan["plan_id"], str)
    assert isinstance(plan["role"], str)
    assert isinstance(plan["task"], str)
    assert isinstance(plan["findings"], str)
    assert isinstance(plan["risks"], list)
    assert isinstance(plan["sources"], list)

    assert plan["tasks"] and isinstance(plan["tasks"], list)
    for task in plan["tasks"]:
        for field in ("id", "title", "summary", "description", "role", "inputs", "outputs", "constraints"):
            assert field in task

    jsonschema.validate(plan, planner_schema)


def test_planner_task_sufficiency(monkeypatch, planner_schema):
    payload = {
        "plan_id": "PLAN-900",
        "role": "Planner",
        "task": "Outline execution phases",
        "findings": "Baseline",
        "constraints": "",
        "assumptions": "",
        "metrics": "",
        "next_steps": "",
        "risks": [],
        "sources": [],
        "tasks": [
            {
                "id": "T01",
                "title": "Architecture work-up",
                "summary": "Outline major subsystems",
                "description": "Draft the system architecture",
                "role": "CTO",
                "inputs": ["Concept brief"],
                "outputs": ["Architecture outline"],
                "constraints": ["Keep design modular"],
            },
            {
                "id": "T02",
                "title": "Lab validation plan",
                "summary": "Design core experiments",
                "description": "Frame early research tasks",
                "role": "Research Scientist",
                "inputs": ["System hypothesis"],
                "outputs": ["Experiment matrix"],
                "constraints": ["Neutral scope"],
            },
            {
                "id": "T03",
                "title": "Compliance outline",
                "summary": "List regulatory checkpoints",
                "description": "Identify certification path",
                "role": "Regulatory",
                "inputs": ["Governance brief"],
                "outputs": ["Compliance checklist"],
                "constraints": ["Policy alignment"],
            },
            {
                "id": "T04",
                "title": "Financial modelling",
                "summary": "Build initial budget",
                "description": "Estimate costs and runway",
                "role": "Finance",
                "inputs": ["Cost assumptions"],
                "outputs": ["Budget model"],
                "constraints": ["Stay within guardrails"],
            },
            {
                "id": "T05",
                "title": "Market sizing",
                "summary": "Assess opportunity",
                "description": "Segment audience",
                "role": "Marketing Analyst",
                "inputs": ["Market research"],
                "outputs": ["Segmentation brief"],
                "constraints": ["Neutral messaging"],
            },
            {
                "id": "T06",
                "title": "Prior art scan",
                "summary": "Survey existing filings",
                "description": "Collect comparable patents",
                "role": "IP Analyst",
                "inputs": ["Search terms"],
                "outputs": ["Prior art summary"],
                "constraints": ["Generic references"],
            },
            {
                "id": "T07",
                "title": "Hiring plan",
                "summary": "Plan team growth",
                "description": "Map staffing requirements",
                "role": "HRM",
                "inputs": ["Org design brief"],
                "outputs": ["Hiring roadmap"],
                "constraints": ["Confidential"],
            },
            {
                "id": "T08",
                "title": "Materials evaluation",
                "summary": "Review candidate materials",
                "description": "Assess structural options",
                "role": "Materials Engineer",
                "inputs": ["Performance targets"],
                "outputs": ["Material shortlist"],
                "constraints": ["Neutral documentation"],
            },
            {
                "id": "T09",
                "title": "Verification plan",
                "summary": "Outline system tests",
                "description": "Define QA approach",
                "role": "QA",
                "inputs": ["Acceptance criteria"],
                "outputs": ["Test plan"],
                "constraints": ["No idea references"],
            },
            {
                "id": "T10",
                "title": "Simulation prep",
                "summary": "Set up models",
                "description": "Plan simulation activities",
                "role": "Simulation",
                "inputs": ["System parameters"],
                "outputs": ["Simulation roadmap"],
                "constraints": ["Model neutrality"],
            },
            {
                "id": "T11",
                "title": "Iterative planning",
                "summary": "Define feedback loops",
                "description": "Coordinate next steps",
                "role": "Dynamic Specialist",
                "inputs": ["Team updates"],
                "outputs": ["Iteration plan"],
                "constraints": ["Neutral communication"],
            },
            {
                "id": "T12",
                "title": "Provisional filing",
                "summary": "Outline patent strategy",
                "description": "Draft filing components",
                "role": "Patent",
                "inputs": ["Innovation notes"],
                "outputs": ["Draft structure"],
                "constraints": ["Generic legal language"],
            },
        ],
    }

    class DummyResult:
        def __init__(self, text: str) -> None:
            self.content = text
            self.raw: dict[str, Any] = {}

    def fake_complete(system_prompt: str, user_prompt: str, **kwargs: Any) -> DummyResult:
        return DummyResult(json.dumps(payload))

    monkeypatch.setattr("core.agents.base_agent.complete", fake_complete)
    monkeypatch.setattr(feature_flags, "POLICY_AWARE_PLANNING", False)
    monkeypatch.setattr(feature_flags, "SAFETY_ENABLED", False)
    monkeypatch.setattr(feature_flags, "FILTERS_STRICT_MODE", False)

    agent = PlannerAgent("Planner", "test-model")
    result = agent.act("High altitude rescue platform", "Outline execution phases")
    plan = json.loads(result)

    jsonschema.validate(plan, planner_schema)
    assert plan["tasks"]
    assert len(plan["tasks"]) == len(payload["tasks"])

    for task in plan["tasks"]:
        assert task_contains_concrete_detail(task), f"Task {task.get('id')} lacks actionable detail"


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


def test_planner_llm_hints_are_deterministic():
    pf = PromptFactory()
    spec = {
        "role": "Planner",
        "task": "Outline execution phases",
        "inputs": {
            "idea": "Project ChronoGlide",
            "constraints_section": "",
            "risk_section": "",
        },
        "io_schema_ref": "dr_rd/schemas/planner_v1.json",
    }

    prompt = pf.build_prompt(spec)
    hints = prompt.get("llm_hints", {})

    assert hints.get("temperature") is not None
    assert hints["temperature"] == pytest.approx(0.0)
    assert hints.get("top_p") is not None
    assert hints["top_p"] <= 0.2
    assert hints.get("presence_penalty") == pytest.approx(0.0)
    assert hints.get("frequency_penalty") == pytest.approx(0.0)


def test_planner_no_idea_leak(monkeypatch, planner_schema):
    payload = {
        "plan_id": "PLAN-123",
        "role": "Planner",
        "task": "Outline execution phases",
        "findings": "Baseline",
        "constraints": "",
        "assumptions": "",
        "metrics": "",
        "next_steps": "",
        "risks": [],
        "sources": [],
        "tasks": [
            {
                "id": "T01",
                "title": "ChronoGlide Drone Pro feasibility",
                "summary": "Assess ChronoGlide Drone Pro viability",
                "description": "Design the ChronoGlide Drone Pro control stack",
                "role": "CTO",
                "inputs": ["ChronoGlide Drone Pro concept deck"],
                "outputs": ["ChronoGlide Drone Pro architecture outline"],
                "constraints": ["ChronoGlide Drone Pro budget"],
            }
        ],
    }

    class DummyResult:
        def __init__(self, text: str) -> None:
            self.content = text
            self.raw = {}

    def fake_complete(system_prompt: str, user_prompt: str, **kwargs: Any) -> DummyResult:
        return DummyResult(json.dumps(payload))

    monkeypatch.setattr("core.agents.base_agent.complete", fake_complete)
    monkeypatch.setattr(feature_flags, "POLICY_AWARE_PLANNING", False)
    monkeypatch.setattr(feature_flags, "SAFETY_ENABLED", False)
    monkeypatch.setattr(feature_flags, "FILTERS_STRICT_MODE", False)

    agent = PlannerAgent("Planner", "test-model")
    result = agent.act(
        "ChronoGlide Drone Pro: Rapid-response UAV for mountain rescue",
        "Outline execution phases",
    )
    plan = json.loads(result)

    jsonschema.validate(plan, planner_schema)

    sensitive_terms = ["ChronoGlide", "Drone Pro"]
    task = plan["tasks"][0]
    for field in ("title", "summary", "description"):
        value = task[field]
        assert isinstance(value, str)
        assert all(term not in value for term in sensitive_terms)
        assert "the system" in value

    for field in ("inputs", "outputs", "constraints"):
        values = task[field]
        assert isinstance(values, list)
        joined = " ".join(values)
        assert all(term not in joined for term in sensitive_terms)
        assert "the system" in joined


def test_planner_auto_retry_success(monkeypatch, planner_schema):
    success_payload = {
        "plan_id": "PLAN-001",
        "role": "Planner",
        "task": "Outline execution phases",
        "findings": "Baseline",
        "constraints": "",
        "assumptions": "",
        "metrics": "",
        "next_steps": "Roadmap",
        "risks": ["Schedule"],
        "sources": ["Internal"],
        "tasks": [
            {
                "id": "T01",
                "title": "Define milestones",
                "summary": "Set neutral milestones",
                "description": "Draft milestones for the system rollout",
                "role": "CTO",
                "inputs": ["Planning brief"],
                "outputs": ["Milestone chart"],
                "constraints": ["Budget cap"],
            }
        ],
    }

    class DummyResult:
        def __init__(self, text: str) -> None:
            self.content = text
            self.raw = {}

    call_counter = {"count": 0}

    def fake_complete(system_prompt: str, user_prompt: str, **kwargs: Any) -> DummyResult:
        call_counter["count"] += 1
        if call_counter["count"] == 1:
            return DummyResult("not valid json")
        return DummyResult(json.dumps(success_payload))

    monkeypatch.setattr("core.agents.base_agent.complete", fake_complete)
    monkeypatch.setattr(feature_flags, "POLICY_AWARE_PLANNING", False)
    monkeypatch.setattr(feature_flags, "SAFETY_ENABLED", False)
    monkeypatch.setattr(feature_flags, "FILTERS_STRICT_MODE", False)

    agent = PlannerAgent("Planner", "test-model")
    result = agent.act("Nebula concept", "Outline execution phases")
    plan = json.loads(result)

    assert call_counter["count"] == 2
    jsonschema.validate(plan, planner_schema)
    assert plan["plan_id"] == "PLAN-001"
    assert plan["tasks"]
    assert plan["tasks"][0]["id"] == "T01"

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


def test_reflection_prompt_factory_strips_idea_context():
    pf = PromptFactory()
    payload = {
        "CTO": {"summary": "Not determined", "findings": "", "risks": []},
        "Regulatory": {"summary": "Pending", "findings": "", "risks": []},
    }
    task_str = json.dumps(payload)
    inputs = prepare_prompt_inputs(payload, idea="NebulaLink Beacon Series")
    inputs["task_payload"] = task_str
    spec = {
        "role": "Reflection",
        "task": task_str,
        "inputs": inputs,
        "io_schema_ref": "dr_rd/schemas/reflection_v1.json",
    }

    prompt = pf.build_prompt(spec)

    assert "idea" not in spec["inputs"]
    serialized_prompt = json.dumps(prompt)
    assert "NebulaLink" not in serialized_prompt
    assert "Beacon Series" not in serialized_prompt


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


def test_compartment_check_flags_scope_violation():
    config = {
        "idea": "ChronoGlide Drone Pro: Rapid-response UAV for mountain rescue",
        "role_names": ["CTO", "Marketing Analyst", "Planner"],
        "current_role": "Materials Engineer",
    }

    idea_payload = {
        "analysis": "The ChronoGlide Drone Pro branding should remain hidden from downstream teams.",
        "summary": "Maintain compartmentalized briefing materials.",
    }

    ok, reason, details = compartment_check(idea_payload, config)
    assert ok is False
    assert reason == "idea_reference"
    assert details["action"] == "revise"
    assert details["matches"]
    assert any(match["reason"] == "idea_reference" for match in details["matches"])
    assert any(
        "ChronoGlide" in match.get("snippet", "")
        for match in details["matches"]
        if match["reason"] == "idea_reference"
    )

    cross_scope_payload = {
        "summary": "Coordinate with the CTO on the device integration before handing off to other teams.",
        "findings": "No blockers identified.",
    }

    redact_config = dict(config)
    redact_config["on_violation"] = "redact"

    ok, reason, details = compartment_check(cross_scope_payload, redact_config)
    assert ok is False
    assert reason == "cross_role_reference"
    assert details["action"] == "redact"
    assert any(match["reason"] == "cross_role_reference" for match in details["matches"])
    sanitized = details.get("sanitized")
    assert isinstance(sanitized, dict)
    assert "[REDACTED_SCOPE]" in sanitized["summary"]
    assert "CTO" not in sanitized["summary"]

    ok, reason, details = compartment_check(
        {"analysis": "Focus on the assigned subsystem deliverable only."}, config
    )
    assert ok is True
    assert reason == ""
    assert details["matches"] == []
