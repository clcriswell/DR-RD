import json
import pytest

from core.agents.prompt_agent import PromptFactoryAgent
from core.agents.base_agent import LLMRoleAgent
from config import feature_flags


class DummyAgent(PromptFactoryAgent):
    """Minimal agent for testing auto-correction."""
    pass


class DummyFactory:
    def __init__(self, schema_path: str):
        self.schema_path = schema_path

    def build_prompt(self, spec):
        return {
            "system": "sys",
            "user": "user",
            "io_schema_ref": self.schema_path,
            "retrieval": {"enabled": False, "policy": "NONE"},
            "llm_hints": {},
        }


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("{\"a\": \"b\",}", {"a": "b"}),
        ("{a: \"b\"}", {"a": "b"}),
        ("```json\n{\"a\": \"b\"}\n```", {"a": "b"}),
    ],
)

def test_auto_correction_no_fallback(tmp_path, monkeypatch, raw, expected):
    monkeypatch.setattr(feature_flags, "EVALUATORS_ENABLED", False)
    schema = {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))

    calls: list[int] = []

    def fake_act(self, system, user, **kwargs):  # type: ignore[override]
        calls.append(1)
        return raw

    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)

    agent = DummyAgent("gpt-4o-mini")
    agent._factory = DummyFactory(str(schema_path))

    result = agent.run_with_spec({"role": "Tester"})
    assert len(calls) == 1
    assert result.fallback_used is False
    assert json.loads(result) == expected
