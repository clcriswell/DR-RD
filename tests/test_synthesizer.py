from unittest.mock import Mock, patch
import os
import pytest
from agents.synthesizer import compose_final_proposal


def make_openai_response(text: str):
    mock_choice = Mock()
    mock_choice.message = Mock(content=text)
    return Mock(choices=[mock_choice])


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch('openai.chat.completions.create')
def test_compose_final_proposal(mock_create):
    fake_response = "Summary of project\n\n## Mechanical Systems Lead\nDetails here\n\n## Simulation Results\nData"
    mock_create.return_value = make_openai_response(fake_response)
    answers = {
        "Mechanical Systems Lead": "design",
        "Optical Systems Engineer": "optics",
        "AI R&D Coordinator": "ai tasks",
    }
    result = compose_final_proposal("idea", answers, include_simulations=True)
    assert result.startswith("Summary")
    assert "## Mechanical Systems Lead" in result
