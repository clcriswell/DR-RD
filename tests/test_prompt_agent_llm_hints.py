import json

import core.agents.base_agent as base_agent
from config import feature_flags
from core.agents.prompt_agent import PromptFactoryAgent


def test_prompt_factory_agent_expands_llm_hints(monkeypatch, tmp_path):
    agent = PromptFactoryAgent("Test", model="gpt-4o-mini")

    schema_path = tmp_path / "schema.json"
    schema_path.write_text("{}", encoding="utf-8")

    prompt_data = {
        "system": "sys",
        "user": "u",
        "io_schema_ref": str(schema_path),
        "llm_hints": {"temperature": 0.3},
        "evaluation_hooks": [],
    }

    monkeypatch.setattr(agent._factory, "build_prompt", lambda spec: prompt_data)
    monkeypatch.setattr(feature_flags, "EVALUATORS_ENABLED", False)

    captured = {}

    def fake_complete(system, user, *, model, **kwargs):
        captured.update(kwargs)

        class Dummy:
            content = json.dumps({})
            raw = {}

        return Dummy()

    monkeypatch.setattr(base_agent, "complete", fake_complete)

    agent.run_with_spec({})
    assert "temperature" in captured
    assert "llm_hints" not in captured
