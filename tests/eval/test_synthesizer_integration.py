import json

import pytest

from core.agents.synthesizer_agent import SynthesizerAgent
from core.agents.prompt_agent import PromptFactoryAgent

from dr_rd.reporting import composer


@pytest.fixture(autouse=True)
def _stub_synthesizer_completion(monkeypatch):
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
                "confidence": 1.0,
                "contradictions": [],
            }
        )

    monkeypatch.setattr(PromptFactoryAgent, "run_with_spec", fake_run_with_spec)


def test_contradictions_detection_and_confidence():
    conflicting_answers = {
        "CTO": {"decision": "Proceed", "summary": "Ready"},
        "Regulatory": {"decision": "Hold", "summary": "Pending"},
        "Finance": {"decision": "Proceed"},
        "QA": {"summary": "Not determined"},
    }

    clean_answers = {
        "CTO": {"decision": "Proceed", "summary": "Ready"},
        "Regulatory": {"decision": "Proceed", "summary": "Ready"},
    }

    agent = SynthesizerAgent("model")

    conflicting = json.loads(agent.act("idea", conflicting_answers))
    assert conflicting["contradictions"], "Expected contradictions to be detected"
    assert any("decision" in msg for msg in conflicting["contradictions"])
    assert any("Not determined" in msg for msg in conflicting["contradictions"])
    assert conflicting["confidence"] <= 0.6

    clean = json.loads(agent.act("idea", clean_answers))
    assert clean["contradictions"] == []
    assert clean["confidence"] == pytest.approx(1.0)

    report_spec = {"planner": {"tasks": []}, "report_id": "r-1", "title": "Run"}
    report = composer.compose(report_spec, {"agents": [], "synth": conflicting})

    assert report.get("contradictions") == conflicting["contradictions"]
    assert report.get("confidence") == conflicting["confidence"]
