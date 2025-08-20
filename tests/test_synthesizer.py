from unittest.mock import patch
import os
import pytest
from core.agents.synthesizer_agent import compose_final_proposal
from core.llm import ChatResult


def make_chat_result(text: str):
    return ChatResult(content=text, raw={"usage": {"prompt_tokens": 1, "completion_tokens": 1}})


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("core.agents.synthesizer_agent.make_visuals_for_project", return_value=[{"kind": "schematic", "url": "u", "caption": "S"}])
@patch("core.agents.synthesizer_agent.complete")
def test_compose_final_proposal(mock_complete, _mock_vis):
    fake_response = (
        "## Executive Summary\nOverview\n\n"
        "## Bill of Materials\n|Component|Quantity|Specs|\n|---|---|---|\n|Part|1|Spec|\n\n"
        "## Step-by-Step Instructions\n1. Do X\n\n"
        "## Simulation & Test Results\nNone"
    )
    mock_complete.return_value = make_chat_result(fake_response)
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
