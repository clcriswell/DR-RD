from unittest.mock import Mock, patch
import os
from agents.planner_agent import PlannerAgent


def make_openai_response(text: str):
    mock_choice = Mock()
    mock_choice.message = Mock(content=text)
    return Mock(choices=[mock_choice])


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch('agents.planner_agent.openai.chat.completions.create')
def test_planner_agent_returns_dict_without_response_format(mock_create):
    """Legacy models should not receive the response_format parameter."""
    mock_create.return_value = make_openai_response('{"X": "Y"}')
    agent = PlannerAgent("gpt-4")
    result = agent.run('idea', 'task')

    assert result == {"X": "Y"}
    # Ensure response_format was not supplied for unsupported models
    _, kwargs = mock_create.call_args
    assert "response_format" not in kwargs


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch('agents.planner_agent.openai.chat.completions.create')
def test_planner_agent_uses_response_format_for_new_models(mock_create):
    mock_create.return_value = make_openai_response('{"X": "Y"}')
    agent = PlannerAgent("gpt-4o-mini")
    agent.run('idea', 'task')

    _, kwargs = mock_create.call_args
    assert kwargs.get("response_format") == {"type": "json_object"}


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch('agents.planner_agent.openai.chat.completions.create')
def test_planner_agent_handles_truncated_json(mock_create):
    text = '{ "A": "B", "C": "D", "E": "F'
    mock_create.return_value = make_openai_response(text)
    agent = PlannerAgent("gpt-4o")
    result = agent.run('idea', 'task')

    assert result == {"A": "B", "C": "D"}
