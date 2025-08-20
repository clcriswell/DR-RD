import json
import os
from unittest.mock import patch

os.environ.setdefault("OPENAI_API_KEY", "test")

from core.agents.hrm_agent import HRMAgent
from core.agents.planner_agent import PlannerAgent
from core.agents.reflection_agent import ReflectionAgent
from core.orchestrator import orchestrate


def _res(text):
    return type("R", (), {"content": text})()


@patch("core.agents.base_agent.complete", return_value=_res('{"roles":["CTO"]}'))
def test_hrm_returns_roles_json(mock_complete):
    agent = HRMAgent("HRM", "gpt-5")
    out = agent.act("sys", "idea")
    data = json.loads(out)
    assert isinstance(data.get("roles"), list)


@patch("core.agents.base_agent.complete", return_value=_res('{"tasks":[{"task":"T","domain":"D"}]}'))
def test_planner_returns_tasks_json(mock_complete):
    agent = PlannerAgent("Planner", "gpt-5")
    out = agent.act("sys", "idea")
    data = json.loads(out)
    assert isinstance(data.get("tasks"), list)
    assert "task" in data["tasks"][0]
    assert set(data["tasks"][0].keys()) <= {"task", "domain"}


@patch("core.agents.base_agent.complete", return_value=_res('["follow up"]'))
def test_reflection_returns_list(mock_complete):
    agent = ReflectionAgent("Reflection", "gpt-5")
    out = agent.act("sys", "summary")
    data = json.loads(out)
    assert isinstance(data, list)


@patch("core.agents.base_agent.complete", return_value=_res('no further tasks'))
def test_reflection_returns_no_tasks(mock_complete):
    agent = ReflectionAgent("Reflection", "gpt-5")
    out = agent.act("sys", "summary")
    assert out.strip().lower() == "no further tasks"


@patch(
    "core.agents.base_agent.complete",
    side_effect=[
        _res('{"roles":["ResearchScientist"]}'),
        _res('{"tasks":[{"task":"do research","domain":"research"}]}'),
        _res("result"),
        _res("no further tasks"),
        _res("final plan"),
    ],
)
def test_orchestrate_smoke(mock_complete):
    result = orchestrate("Microscope that uses quantum entanglement")
    assert isinstance(result, str) and result
