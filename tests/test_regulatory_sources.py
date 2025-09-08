import json

import jsonschema

from core.agents.prompt_agent import PromptFactoryAgent
from core.agents.base_agent import LLMRoleAgent
from config import feature_flags


def _spec():
    return {"role": "Regulatory", "inputs": {"idea": "", "task": ""}}


def _schema():
    with open("dr_rd/schemas/regulatory_v2.json", encoding="utf-8") as fh:
        return json.load(fh)


def _run(raw: str, monkeypatch) -> str:
    monkeypatch.setattr(feature_flags, "EVALUATORS_ENABLED", False)

    def fake_act(self, system, user, response_format=None, **kwargs):
        return raw

    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)
    agent = PromptFactoryAgent("gpt-4o-mini")
    return agent.run_with_spec(_spec())


def test_markdown_link_sanitized(monkeypatch):
    raw = json.dumps(
        {
            "role": "Regulatory",
            "task": "T1",
            "summary": "",
            "findings": "",
            "risks": [],
            "next_steps": [],
            "sources": [
                "([yjolt.org](https://yjolt.org/blog/establishing-legal-ethical-framework-quantum-technology?utm_source=openai))"
            ],
        }
    )
    result = _run(raw, monkeypatch)
    data = json.loads(result)
    jsonschema.validate(data, _schema())
    assert data["sources"][0]["title"] == "yjolt.org"
    assert data["sources"][0]["url"].startswith("https://yjolt.org")


def test_missing_keys_filled(monkeypatch):
    raw = json.dumps(
        {
            "role": "Regulatory",
            "task": "T1",
            "summary": "",
            "findings": "",
            "risks": [],
            "next_steps": [],
            "sources": [{"url": "https://example.com"}],
        }
    )
    result = _run(raw, monkeypatch)
    data = json.loads(result)
    jsonschema.validate(data, _schema())
    assert data["sources"][0]["id"] == "https://example.com"
    assert data["sources"][0]["title"] == "https://example.com"


def test_plain_string_source(monkeypatch):
    raw = json.dumps(
        {
            "role": "Regulatory",
            "task": "T1",
            "summary": "",
            "findings": "",
            "risks": [],
            "next_steps": [],
            "sources": ["https://plain.example"],
        }
    )
    result = _run(raw, monkeypatch)
    data = json.loads(result)
    jsonschema.validate(data, _schema())
    assert data["sources"][0]["id"] == "https://plain.example"
    assert data["sources"][0]["url"] == "https://plain.example"
