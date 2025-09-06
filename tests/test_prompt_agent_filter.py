import json

import pytest

from config import feature_flags
from core.agents.base_agent import LLMRoleAgent
from core.agents.prompt_agent import PromptFactoryAgent


class DummyAgent(PromptFactoryAgent):
    """PromptFactoryAgent with a static prompt factory."""
    pass


def test_extra_keys_trimmed(monkeypatch, tmp_path):
    schema = {
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "object", "properties": {"c": {"type": "number"}}},
            "arr": {
                "type": "array",
                "items": {"type": "object", "properties": {"x": {"type": "number"}}},
            },
        },
        "additionalProperties": False,
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")

    prompt_data = {
        "system": "sys",
        "user": "u",
        "io_schema_ref": str(schema_path),
        "llm_hints": {},
        "retrieval_plan": {},
        "evaluation_hooks": [],
    }

    agent = DummyAgent("tester", model="gpt-4o-mini")
    agent._factory = type("F", (), {"build_prompt": lambda self, spec: prompt_data})()
    monkeypatch.setattr(feature_flags, "EVALUATORS_ENABLED", False)

    response = {
        "a": 1,
        "b": {"c": 2, "d": 3},
        "arr": [{"x": 1, "y": 2}, {"x": 3, "z": 4}],
        "extra": 5,
    }

    def fake_act(self, system, user, **kwargs):
        return json.dumps(response)

    monkeypatch.setattr(LLMRoleAgent, "act", fake_act, raising=False)

    out = agent.run_with_spec({})
    data = json.loads(out)
    assert data == {"a": 1, "b": {"c": 2}, "arr": [{"x": 1}, {"x": 3}]}
    assert "extra" not in data
