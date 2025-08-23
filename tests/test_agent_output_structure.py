import os
from unittest.mock import Mock, patch

import pytest

from core.agents.ai_rd_coordinator_agent import AIResearchDevelopmentCoordinatorAgent
from core.agents.mechanical_systems_lead_agent import MechanicalSystemsLeadAgent
from core.agents.optical_systems_engineer_agent import OpticalSystemsEngineerAgent


def make_openai_response(text: str):
    mock_choice = Mock()
    mock_choice.message = Mock(content=text)
    return Mock(choices=[mock_choice])


AGENTS = [
    MechanicalSystemsLeadAgent,
    OpticalSystemsEngineerAgent,
    AIResearchDevelopmentCoordinatorAgent,
]


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("core.agents.base_agent.call_openai")
@pytest.mark.parametrize("cls", AGENTS)
def test_agent_output_structure(mock_call, cls):
    fake_md = 'Result\n```json\n{"key": 1}\n```'
    mock_call.return_value = {"text": fake_md, "raw": {}}
    agent = cls("gpt-5")
    result = agent.run("idea", "task")
    stripped = result.strip()
    assert stripped.endswith("```")
    assert "```json" in stripped
