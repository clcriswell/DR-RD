from unittest.mock import Mock, patch
import os
from agents.planner_agent import PlannerAgent


def make_openai_response(text: str):
    mock_choice = Mock()
    mock_choice.message = Mock(content=text)
    return Mock(choices=[mock_choice])


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch('openai.chat.completions.create')
def test_planner_agent_returns_dict(mock_create):
    mock_create.return_value = make_openai_response('{"X": "Y"}')
    agent = PlannerAgent("gpt-4")
    result = agent.run('idea', 'task')
    assert result == {"X": "Y"}
