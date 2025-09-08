import json

import jsonschema
import pytest

from core.agents.prompt_agent import PromptFactoryAgent, make_empty_payload
from core.agents.base_agent import LLMRoleAgent

SCHEMAS = [
    "dr_rd/schemas/cto_v2_fallback.json",
    "dr_rd/schemas/regulatory_v2_fallback.json",
    "dr_rd/schemas/marketing_v2_fallback.json",
    "dr_rd/schemas/finance_v2_fallback.json",
    "dr_rd/schemas/research_v2_fallback.json",
    "dr_rd/schemas/materials_engineer_v2_fallback.json",
]


@pytest.mark.parametrize("path", SCHEMAS)
def test_minimal_payload_valid(path):
    with open(path, encoding="utf-8") as fh:
        schema = json.load(fh)
    payload = {"role": "r", "task": "t", "summary": "s"}
    jsonschema.validate(payload, schema)


class DummyAgent(PromptFactoryAgent):
    """Minimal agent for fallback testing."""


def _finance_spec():
    return {
        "role": "Finance",
        "task": "t",
        "inputs": {"idea": "i", "task": "t"},
        "io_schema_ref": "dr_rd/schemas/finance_v2.json",
    }


def test_primary_failure_then_fallback_success(monkeypatch):
    agent = DummyAgent("gpt-4o-mini")
    outputs = iter(
        [
            "not json",
            json.dumps({"role": "Finance", "task": "t", "summary": "ok"}),
        ]
    )

    def fake_act(self, system, user, **kwargs):
        return next(outputs)

    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)
    result = agent.run_with_spec(_finance_spec())
    data = json.loads(result)
    assert result.fallback_used is True
    with open("dr_rd/schemas/finance_v2_fallback.json", encoding="utf-8") as fh:
        schema = json.load(fh)
    jsonschema.validate(data, schema)


def test_primary_and_fallback_failure(monkeypatch):
    agent = DummyAgent("gpt-4o-mini")
    outputs = iter(["bad", "still bad"])

    def fake_act(self, system, user, **kwargs):
        return next(outputs)

    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)
    with open("dr_rd/schemas/finance_v2_fallback.json", encoding="utf-8") as fh:
        schema = json.load(fh)
    expected = make_empty_payload(schema)
    result = agent.run_with_spec(_finance_spec())
    data = json.loads(result)
    assert result.fallback_used is True
    assert data == expected
