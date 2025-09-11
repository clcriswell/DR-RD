import json
import json

from core.agents.synthesizer_agent import compose_final_proposal
from core.agents.prompt_agent import PromptFactoryAgent


def test_images_disabled(monkeypatch):

    def fake_run_with_spec(self, spec, **kwargs):
        return json.dumps(
            {
                "summary": "doc",
                "key_points": [],
                "role": "Synthesizer",
                "task": "compose final report",
                "findings": "",
                "risks": [],
                "next_steps": [],
                "sources": [],
            }
        )

    monkeypatch.setattr(PromptFactoryAgent, "run_with_spec", fake_run_with_spec)

    out = json.loads(compose_final_proposal("idea", {"Role": "Answer"}))
    assert "images" not in out
