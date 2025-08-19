import json
from unittest.mock import patch

from agents.hrm_agent import HRMAgent
from agents.planner_agent import LLMPlannerAgent
from agents.reflection_agent import ReflectionAgent
from core.orchestrator import orchestrate


@patch("agents.base_agent.make_chat", return_value='{"roles":["CTO"]}')
def test_hrm_returns_roles_json(mock_chat):
    agent = HRMAgent("gpt-4o-mini")
    out = agent.act("sys", "idea")
    data = json.loads(out)
    assert isinstance(data.get("roles"), list)


@patch("agents.base_agent.make_chat", return_value='{"tasks":[{"task":"T","domain":"D"}]}')
def test_planner_returns_tasks_json(mock_chat):
    agent = LLMPlannerAgent("gpt-4o-mini")
    out = agent.act("sys", "idea")
    data = json.loads(out)
    assert isinstance(data.get("tasks"), list)
    assert "task" in data["tasks"][0]
    assert set(data["tasks"][0].keys()) <= {"task", "domain"}


@patch("agents.base_agent.make_chat", return_value='["follow up"]')
def test_reflection_returns_list(mock_chat):
    agent = ReflectionAgent("gpt-4o-mini")
    out = agent.act("sys", "summary")
    data = json.loads(out)
    assert isinstance(data, list)


@patch("agents.base_agent.make_chat", return_value='no further tasks')
def test_reflection_returns_no_tasks(mock_chat):
    agent = ReflectionAgent("gpt-4o-mini")
    out = agent.act("sys", "summary")
    assert out.strip().lower() == "no further tasks"


@patch(
    "agents.base_agent.make_chat",
    side_effect=[
        '{"roles":["ResearchScientist"]}',
        '{"tasks":[{"task":"do research","domain":"research"}]}',
        "result",
        "no further tasks",
        "final plan",
    ],
)
def test_orchestrate_smoke(mock_chat):
    result = orchestrate("Microscope that uses quantum entanglement")
    assert isinstance(result, str) and result
