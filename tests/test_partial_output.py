import json

from core.agents.prompt_agent import PromptFactoryAgent
from core.agents.base_agent import LLMRoleAgent


class DummyAgent(PromptFactoryAgent):
    pass


def _spec():
    return {
        "role": "CTO",
        "task": "X",
        "inputs": {"idea": "i", "task": "X"},
        "io_schema_ref": "dr_rd/schemas/cto_v2.json",
    }


def test_missing_keys_autofilled(monkeypatch):
    agent = DummyAgent("gpt-4o-mini")

    def fake_act(self, system, user, **kwargs):  # type: ignore[override]
        return '{"role":"CTO","task":"X","summary":"Feasibility looks okay."}'

    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)
    result = agent.run_with_spec(_spec())
    data = json.loads(result)
    assert result.fallback_used is False
    assert data["summary"] == "Feasibility looks okay."
    assert data["findings"] == "Not determined"
    assert data["risks"] == []
    assert data["next_steps"] == "Not determined"
    assert data["sources"] == []
