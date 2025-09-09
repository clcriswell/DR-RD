import json
import jsonschema

from core.agents.prompt_agent import coerce_types, strip_additional_properties
from core.agents.cto_agent import CTOAgent
from utils.agent_json import clean_json_payload


def test_sanitization_coerces_and_strips():
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "findings": {"type": "string"},
        },
        "required": ["summary", "findings"],
        "additionalProperties": False,
    }
    payload = {"summary": ["a", "b"], "findings": ["x", "y"], "image_query": "img"}
    coerced = coerce_types(payload, schema)
    cleaned = strip_additional_properties(coerced, schema)
    jsonschema.validate(cleaned, schema)
    assert cleaned == {"summary": "a; b", "findings": "x; y"}


def test_clean_payload_sources_string_mode():
    schema = {
        "type": "object",
        "properties": {
            "sources": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["sources"],
        "additionalProperties": False,
    }
    payload = {
        "sources": [
            "plain source",
            {"url": "http://b.com", "extra": 1},
            {"title": "Only Title"},
            {},
            "[Link](http://c.com)",
            5,
        ]
    }
    cleaned = clean_json_payload(payload, schema)
    cleaned = coerce_types(cleaned, schema)
    cleaned = strip_additional_properties(cleaned, schema)
    jsonschema.validate(cleaned, schema)
    assert cleaned == {
        "sources": [
            "plain source",
            "http://b.com",
            "Only Title",
            "Link: http://c.com",
        ]
    }


def test_clean_payload_sources_object_mode_and_types():
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "next_steps": {"type": "array", "items": {"type": "string"}},
            "sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": ["id", "title"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["summary", "tags", "next_steps", "sources"],
        "additionalProperties": False,
    }
    payload = {
        "summary": "- first\n- second",
        "tags": "alpha; beta\n* gamma",
        "sources": [
            "[Paper](http://a.com)",
            "http://b.com",
            {"id": "1", "title": "T1", "url": "http://c.com", "x": 1},
        ],
    }
    cleaned = clean_json_payload(payload, schema)
    cleaned = coerce_types(cleaned, schema)
    cleaned = strip_additional_properties(cleaned, schema)
    jsonschema.validate(cleaned, schema)
    assert cleaned == {
        "summary": "first; second",
        "tags": ["alpha", "beta", "gamma"],
        "next_steps": [],
        "sources": [
            {"id": "paper", "title": "Paper", "url": "http://a.com"},
            {"id": "http://b.com", "title": "http://b.com", "url": "http://b.com"},
            {"id": "1", "title": "T1", "url": "http://c.com"},
        ],
    }


def test_cto_agent_no_tool_result():
    class DummyCTO(CTOAgent):
        def __init__(self):
            super().__init__("dummy")

        def run_with_spec(self, spec, **kwargs):  # type: ignore[override]
            return json.dumps(
                {
                    "role": "",
                    "task": "",
                    "summary": "",
                    "findings": "",
                    "risks": [],
                    "next_steps": [],
                    "sources": [],
                }
            )

        def run_tool(self, tool_name, params):  # type: ignore[override]
            return "ok"

    agent = DummyCTO()
    out = agent.act("idea", {"tool_request": {"tool": "t", "params": {}}})
    data = json.loads(out)
    assert "tool_result" not in data
