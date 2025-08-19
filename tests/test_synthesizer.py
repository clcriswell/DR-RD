from unittest.mock import Mock, patch
import os
import pytest
from agents.synthesizer import compose_final_proposal


def make_openai_response(text: str):
    mock_choice = Mock()
    mock_choice.message = Mock(content=text)
    return Mock(choices=[mock_choice])


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("agents.synthesizer.make_visuals_for_project", return_value=[{"kind": "schematic", "url": "u", "caption": "S"}])
@patch('agents.synthesizer.llm_call')
def test_compose_final_proposal(mock_llm, _mock_vis):
    fake_response = (
        "## Executive Summary\nOverview\n\n"
        "## Bill of Materials\n|Component|Quantity|Specs|\n|---|---|---|\n|Part|1|Spec|\n\n"
        "## Step-by-Step Instructions\n1. Do X\n\n"
        "## Simulation & Test Results\nNone"
    )
    mock_llm.return_value = make_openai_response(fake_response)
    answers = {
        "Mechanical Systems Lead": "design",
        "Optical Systems Engineer": "optics",
        "AI R&D Coordinator": "ai tasks",
    }
    result = compose_final_proposal("idea", answers, include_simulations=True)
    assert "## Executive Summary" in result["document"]
    assert "## Step-by-Step Instructions" in result["document"]
    assert result["images"][0]["url"] == "u"
    assert result["test"] is False
