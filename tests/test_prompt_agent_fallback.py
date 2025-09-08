import json

from core.agents.prompt_agent import PromptFactoryAgent
from core.agents.base_agent import LLMRoleAgent


class DummyAgent(PromptFactoryAgent):
    """Minimal agent for testing."""
    pass


def _spec():
    return {
        "role": "Marketing Analyst",
        "task": "t",
        "inputs": {"idea": "i", "task": "t"},
        "io_schema_ref": "dr_rd/schemas/marketing_v2.json",
    }


def test_fallback_produces_valid_json(monkeypatch):
    agent = DummyAgent("gpt-4o-mini")
    outputs = iter([
        "not json",
        json.dumps({"role": "Marketing Analyst", "task": "t", "summary": "ok"}),
    ])

    def fake_act(self, system, user, **kwargs):
        return next(outputs)

    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)
    result = agent.run_with_spec(_spec())
    assert isinstance(result, str)
    assert result.fallback_used is True
    data = json.loads(result)
    assert data["summary"] == "ok"


def test_fallback_returns_placeholder_on_failure(monkeypatch):
    agent = DummyAgent("gpt-4o-mini")
    outputs = iter(["bad", "still bad"])

    def fake_act(self, system, user, **kwargs):
        return next(outputs)

    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)
    result = agent.run_with_spec(_spec())
    data = json.loads(result)
    assert result.fallback_used is True
    assert {"role", "task", "summary"}.issubset(data)
    assert data["summary"] == "Not determined"
