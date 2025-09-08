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
    required_calls: list[list[str] | None] = []

    def fake_act(self, system, user, **kwargs):
        fmt = (
            kwargs.get("response_format", {})
            .get("json_schema", {})
            .get("schema", {})
        )
        required_calls.append(fmt.get("required"))
        return next(outputs)

    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)
    result = agent.run_with_spec(_spec())
    assert isinstance(result, str)
    assert result.fallback_used is True
    data = json.loads(result)
    assert data["summary"] == "ok"
    # first call uses full schema, second call uses fallback
    assert required_calls[0] != required_calls[1]
    assert required_calls[1] == ["role", "task", "summary"]


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
