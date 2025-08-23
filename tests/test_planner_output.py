import json
import os
from unittest.mock import Mock, patch

import pytest

from config.agent_models import AGENT_MODEL_MAP
from core.agents.planner_agent import PlannerAgent


def make_openai_response(text: str):
    mock_choice = Mock()
    mock_choice.message = Mock(content=text)
    return Mock(choices=[mock_choice])


ALLOWED_ROLES = set(AGENT_MODEL_MAP.keys()) - {"Planner", "Synthesizer"}


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("core.agents.planner_agent.llm_call")
def test_planner_output_validity(mock_llm):
    mock_llm.return_value = make_openai_response(
        '{"Mechanical Systems Lead": "Design the frame"}'
    )
    agent = PlannerAgent("gpt-5")
    result = agent.run(
        "a quantum entangled laser alignment tool with an FPGA controller",
        "Develop a plan",
    )

    assert isinstance(result, dict)
    assert result
    assert set(result.keys()).issubset(ALLOWED_ROLES)
