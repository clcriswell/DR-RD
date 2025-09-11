import json
import os
from unittest.mock import patch

import pytest

from core.agents.synthesizer_agent import compose_final_proposal
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
