from unittest.mock import Mock, patch
import os
from core.agents.planner_agent import PlannerAgent


def make_openai_response(text: str):
    mock_choice = Mock()
    mock_choice.message = Mock(content=text)
    return Mock(choices=[mock_choice])


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch('core.agents.planner_agent.llm_call')
def test_planner_agent_uses_response_format(mock_llm):
    """Modern models should use the response_format parameter."""
    mock_llm.return_value = make_openai_response('{"X": "Y"}')
    agent = PlannerAgent("gpt-5")
    result = agent.run('idea', 'task')

    assert result == {"X": "Y"}
    _, kwargs = mock_llm.call_args
    assert kwargs.get("response_format") == {"type": "json_object"}


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch('core.agents.planner_agent.llm_call')
def test_planner_agent_handles_truncated_json(mock_llm):
    text = '{ "A": "B", "C": "D", "E": "F'
    mock_llm.return_value = make_openai_response(text)
    agent = PlannerAgent("gpt-5")
    result = agent.run('idea', 'task')

    assert result == {"A": "B", "C": "D"}
