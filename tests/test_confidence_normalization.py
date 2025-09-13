import json
import os
from unittest.mock import patch

import pytest

from core.agents.confidence import normalize_confidence
from core.agents.synthesizer_agent import compose_final_proposal
from core.agents.prompt_agent import PromptFactoryAgent


@pytest.mark.parametrize(
    "text,expected",
    [
        ("High confidence", 0.9),
        ("Moderate confidence", 0.6),
        ("Low confidence", 0.3),
        ("unknown", 0.5),
    ],
)
def test_normalize_confidence_textual(text, expected):
    assert normalize_confidence(text) == expected


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
def test_synthesizer_converts_confidence(monkeypatch):
    def fake_act(self, system, user, response_format=None, **kwargs):
        return json.dumps(
            {
                "summary": "Overview",
                "key_points": [],
                "role": "Synthesizer",
                "task": "compose final report",
                "findings": "analysis",
                "risks": [],
                "next_steps": [],
                "confidence": "High confidence in market demand",
                "sources": [],
            }
        )

    monkeypatch.setattr(PromptFactoryAgent, "act", fake_act)
    out = compose_final_proposal("idea", {})
    data = json.loads(out)
    assert data["confidence"] == 0.9


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
def test_synthesizer_preserves_numeric_confidence(monkeypatch):
    def fake_act(self, system, user, response_format=None, **kwargs):
        return json.dumps(
            {
                "summary": "Overview",
                "key_points": [],
                "role": "Synthesizer",
                "task": "compose final report",
                "findings": "analysis",
                "risks": [],
                "next_steps": [],
                "confidence": 0.8,
                "sources": [],
            }
        )

    monkeypatch.setattr(PromptFactoryAgent, "act", fake_act)
    out = compose_final_proposal("idea", {})
    data = json.loads(out)
    assert data["confidence"] == 0.8
