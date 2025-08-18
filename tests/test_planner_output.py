import json
from unittest.mock import Mock, patch
import os
import pytest
from agents.planner_agent import PlannerAgent
from config.agent_models import AGENT_MODEL_MAP


def make_openai_response(text: str):
    mock_choice = Mock()
    mock_choice.message = Mock(content=text)
    return Mock(choices=[mock_choice])


ALLOWED_ROLES = set(AGENT_MODEL_MAP.keys()) - {"Planner", "Synthesizer"}


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch('agents.planner_agent.openai.chat.completions.create')
def test_planner_output_validity(mock_create):
    mock_create.return_value = make_openai_response('{"Mechanical Systems Lead": "Design the frame"}')
    agent = PlannerAgent("gpt-4o")
    result = agent.run("a quantum entangled laser alignment tool with an FPGA controller", "Develop a plan")

    assert isinstance(result, dict)
    assert result
    assert set(result.keys()).issubset(ALLOWED_ROLES)
