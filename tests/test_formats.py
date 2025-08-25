import json
import os
from unittest.mock import patch

from core.agents.hrm_agent import HRMAgent
from core.agents.planner_agent import PlannerAgent
from core.agents.reflection_agent import ReflectionAgent
from core.orchestrator import orchestrate

os.environ.setdefault("OPENAI_API_KEY", "test")


def _res(text):
    return type("R", (), {"content": text})()


@patch("core.agents.base_agent.complete", return_value=_res('{"roles":["CTO"]}'))
def test_hrm_returns_roles_json(mock_complete):
    agent = HRMAgent("HRM", "gpt-5")
    out = agent.act("sys", "idea")
    data = json.loads(out)
    assert isinstance(data.get("roles"), list)


@patch(
    "core.agents.planner_agent.run_planner",
    return_value=({"tasks": [{"task": "T", "domain": "D"}]}, {}),
)
def test_planner_returns_tasks_json(mock_run):
    agent = PlannerAgent("gpt-5")
    out = agent.run("idea", "task")
    assert isinstance(out.get("tasks"), list)
    assert "task" in out["tasks"][0]
    assert set(out["tasks"][0].keys()) <= {"task", "domain"}


@patch("core.agents.base_agent.complete", return_value=_res('["follow up"]'))
def test_reflection_returns_list(mock_complete):
    agent = ReflectionAgent("Reflection", "gpt-5")
    out = agent.act("sys", "summary")
    data = json.loads(out)
    assert isinstance(data, list)


@patch("core.agents.base_agent.complete", return_value=_res("no further tasks"))
def test_reflection_returns_no_tasks(mock_complete):
    agent = ReflectionAgent("Reflection", "gpt-5")
    out = agent.act("sys", "summary")
    assert out.strip().lower() == "no further tasks"


@patch("core.orchestrator.compose_final_proposal", return_value="final plan")
@patch("core.orchestrator.execute_plan", return_value={"Research Scientist": "result"})
@patch(
    "core.orchestrator.generate_plan",
    return_value=[
        {"role": "Research Scientist", "title": "do research", "description": "do research"}
    ],
)
def test_orchestrate_smoke(mock_plan, mock_exec, mock_comp):
    result = orchestrate("Microscope that uses quantum entanglement")
    assert isinstance(result, str) and result
