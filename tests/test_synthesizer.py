import json
import os
from unittest.mock import patch

import pytest

from core.agents.synthesizer_agent import SynthesizerAgent, compose_final_proposal
from core.agents.prompt_agent import PromptFactoryAgent


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
def test_compose_final_proposal_merges_sources(monkeypatch):
    def fake_run_with_spec(self, spec, **kwargs):
        return json.dumps(
            {
                "summary": "Overview",
                "key_points": ["kp"],
                "role": "Synthesizer",
                "task": "compose final report",
                "findings": "analysis",
                "risks": [],
                "next_steps": [],
                "sources": [],
            }
        )

    monkeypatch.setattr(PromptFactoryAgent, "run_with_spec", fake_run_with_spec)
    answers = {"Role": {"findings": "f", "risks": [], "next_steps": [], "sources": [{"url": "u"}]}}
    out = compose_final_proposal("idea", answers)
    data = json.loads(out)
    assert data["summary"] == "Overview"
    assert data["sources"] == [{"url": "u"}]


def _base_synth_response() -> str:
    return json.dumps(
        {
            "summary": "Overview",
            "key_points": [],
            "role": "Synthesizer",
            "task": "compose final report",
            "findings": "analysis",
            "risks": [],
            "next_steps": [],
            "sources": [],
            "confidence": 0.95,
            "contradictions": [],
        }
    )


def test_synthesizer_detects_conflicting_fields(monkeypatch):
    monkeypatch.setattr(PromptFactoryAgent, "run_with_spec", lambda self, spec, **_: _base_synth_response())

    answers = {
        "CTO": {"decision": "Proceed", "summary": "Ready"},
        "Regulatory": {"decision": "Hold", "summary": "Pending review"},
        "Finance": {"decision": "Proceed"},
    }

    agent = SynthesizerAgent("model")
    data = json.loads(agent.act("idea", answers))

    assert any(
        msg.startswith("Conflicting decision: Proceed (CTO, Finance) vs. Hold (Regulatory)")
        for msg in data.get("contradictions", [])
    )
    assert data["confidence"] == pytest.approx(0.6)


def test_synthesizer_flags_placeholders(monkeypatch):
    monkeypatch.setattr(PromptFactoryAgent, "run_with_spec", lambda self, spec, **_: _base_synth_response())

    answers = {
        "QA": {"summary": "Not determined", "notes": "Investigation pending"},
        "Research": {"summary": "Complete", "details": "See {{ placeholder }}"},
    }

    agent = SynthesizerAgent("model")
    data = json.loads(agent.act("idea", answers))

    contradictions = data.get("contradictions", [])
    assert any("QA contains Not determined placeholder" in msg for msg in contradictions)
    assert any("Research contains unresolved template placeholders" in msg for msg in contradictions)
    assert data["confidence"] == pytest.approx(0.6)
