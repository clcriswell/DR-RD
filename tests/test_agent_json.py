import json

import jsonschema
import pytest

from utils.agent_json import (
    AgentOutputFormatError,
    clean_json_payload,
    extract_json_strict,
)


def test_repair_markdown_fences():
    txt = "```json\n{\"a\":1}\n```"
    assert extract_json_strict(txt) == {"a": 1}


def test_malformed_json_raises():
    with pytest.raises(AgentOutputFormatError):
        extract_json_strict("```json\n{bad}\n```")


def test_sources_clean_string_array():
    schema = {
        "type": "object",
        "properties": {
            "sources": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["sources"],
        "additionalProperties": False,
    }
    payload = {
        "sources": ["Some reference", {}, "[Title](http://example.com)"]
    }
    cleaned = clean_json_payload(payload, schema)
    jsonschema.validate(cleaned, schema)
    assert cleaned == {
        "sources": ["Some reference", "Title: http://example.com"]
    }


def test_sources_clean_object_array():
    schema = {
        "type": "object",
        "properties": {
            "sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": ["id", "title", "url"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["sources"],
        "additionalProperties": False,
    }
    payload = {
        "sources": ["http://example.com", "[Title](http://a.com)"]
    }
    cleaned = clean_json_payload(payload, schema)
    jsonschema.validate(cleaned, schema)
    assert cleaned == {
        "sources": [
            {
                "id": "http://example.com",
                "title": "http://example.com",
                "url": "http://example.com",
            },
            {"id": "title", "title": "Title", "url": "http://a.com"},
        ]
    }


def test_string_to_array_split():
    schema = {
        "type": "object",
        "properties": {
            "risks": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["risks"],
        "additionalProperties": False,
    }
    payload = {"risks": "Risk1; Risk2\n- Risk3"}
    cleaned = clean_json_payload(payload, schema)
    jsonschema.validate(cleaned, schema)
    assert cleaned == {"risks": ["Risk1", "Risk2", "Risk3"]}


def test_list_to_string_join():
    schema = {
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
        "additionalProperties": False,
    }
    payload = {"summary": ["Point A", "Point B"]}
    cleaned = clean_json_payload(payload, schema)
    jsonschema.validate(cleaned, schema)
    assert cleaned == {"summary": "Point A; Point B"}


def test_unknown_keys_removed():
    schema = {
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
        "additionalProperties": False,
    }
    payload = {"summary": "ok", "foo": "bar"}
    cleaned = clean_json_payload(payload, schema)
    jsonschema.validate(cleaned, schema)
    assert cleaned == {"summary": "ok"}


def test_tool_result_removed():
    schema = {
        "type": "object",
        "properties": {
            "role": {"type": "string"},
            "task": {"type": "string"},
            "summary": {"type": "string"},
            "findings": {"type": "string"},
            "risks": {"type": "array", "items": {"type": "string"}},
            "next_steps": {"type": "array", "items": {"type": "string"}},
            "sources": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "role",
            "task",
            "summary",
            "findings",
            "risks",
            "next_steps",
            "sources",
        ],
        "additionalProperties": False,
    }
    payload = {
        "role": "CTO",
        "task": "t",
        "summary": "s",
        "findings": "f",
        "risks": [],
        "next_steps": ["n"],
        "sources": [],
        "tool_result": {"x": 1},
    }
    cleaned = clean_json_payload(payload, schema)
    jsonschema.validate(cleaned, schema)
    assert "tool_result" not in cleaned


def test_missing_field_padding_marketing():
    with open("dr_rd/schemas/marketing_v2.json", encoding="utf-8") as fh:
        schema = json.load(fh)
    payload = {
        "role": "Marketing Analyst",
        "task": "t",
        "summary": "s",
    }
    cleaned = clean_json_payload(payload, schema)
    jsonschema.validate(cleaned, schema)
    assert cleaned["findings"] == "Not determined"
    assert cleaned["next_steps"] == []
    assert cleaned["risks"] == []
    assert cleaned["sources"] == []
