from unittest.mock import Mock, patch
import os
import pytest
from agents.mechanical_systems_lead_agent import MechanicalSystemsLeadAgent
from agents.optical_systems_engineer_agent import OpticalSystemsEngineerAgent
from agents.ai_rd_coordinator_agent import AIResearchDevelopmentCoordinatorAgent

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
@patch('agents.base_agent.llm_call')
@pytest.mark.parametrize("cls", AGENTS)
def test_agent_output_structure(mock_llm, cls):
    fake_md = "Result\n```json\n{\"key\": 1}\n```"
    mock_llm.return_value = make_openai_response(fake_md)
    agent = cls("gpt-4o")
    result = agent.run("idea", "task")
    stripped = result.strip()
    assert stripped.endswith("```")
    assert "```json" in stripped

