from unittest.mock import Mock, patch
import os

from agents.planner_agent import PlannerAgent
from config.feature_flags import EVALUATOR_MIN_OVERALL


def make_openai_response(text: str):
    mock_choice = Mock()
    mock_choice.message = Mock(content=text)
    return Mock(choices=[mock_choice])


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch('agents.planner_agent.llm_call')
def test_planner_adds_remediation_task(mock_llm):
    mock_llm.return_value = make_openai_response('{"updated_tasks": []}')
    agent = PlannerAgent("gpt-4o-mini")
    workspace = {"tasks": [], "scorecard": {"overall": EVALUATOR_MIN_OVERALL - 0.1, "metrics": {}}}
    tasks = agent.revise_plan(workspace)
    assert any("Improve" in t["task"] or "Address" in t["task"] for t in tasks)
