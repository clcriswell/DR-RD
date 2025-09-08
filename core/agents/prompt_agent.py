from __future__ import annotations

import json
import os
from typing import Any

import jsonschema

from config import feature_flags
from core.agents.base_agent import LLMRoleAgent
from core.llm_client import responses_json_schema_from_file
from dr_rd.prompting.prompt_factory import PromptFactory
from dr_rd.prompting.prompt_registry import RetrievalPolicy
from utils.logging import logger


class AgentRunResult(str):
    """String result carrying a fallback flag."""

    fallback_used: bool

    def __new__(cls, value: str, fallback_used: bool = False):
        obj = str.__new__(cls, value)
        obj.fallback_used = fallback_used
        return obj


def coerce_types(data: Any, schema: dict) -> Any:
    """Coerce list values into strings when schema expects string."""
    if not isinstance(schema, dict):
        return data
    if schema.get("type") == "string" and isinstance(data, list):
        if all(isinstance(x, str) for x in data):
            return "; ".join(data)
        return data
    if isinstance(data, dict):
        props = schema.get("properties", {}) or {}
        return {k: coerce_types(v, props.get(k, {})) for k, v in data.items()}
    if isinstance(data, list):
        item_schema = schema.get("items", {}) or {}
        return [coerce_types(item, item_schema) for item in data]
    return data


def strip_additional_properties(data: Any, schema: dict) -> Any:
    """Recursively remove keys not defined in the schema."""
    if not isinstance(schema, dict):
        return data
    if isinstance(data, dict):
        props = schema.get("properties", {}) or {}
        new: dict[str, Any] = {}
        for key, value in data.items():
            if key in props:
                new[key] = strip_additional_properties(value, props[key])
        return new
    if isinstance(data, list):
        item_schema = schema.get("items", {}) or {}
        return [strip_additional_properties(item, item_schema) for item in data]
    return data


def _fallback_schema_path(path: str) -> str:
    root, ext = os.path.splitext(path)
    return f"{root}_fallback{ext}"


def make_empty_payload(schema: dict) -> dict[str, Any]:
    props = schema.get("properties", {}) or {}
    payload: dict[str, Any] = {}
    for key, prop in props.items():
        t = prop.get("type")
        if isinstance(t, list):
            if "array" in t:
                payload[key] = []
            elif "object" in t:
                payload[key] = {}
            else:
                payload[key] = ""
        elif t == "array":
            payload[key] = []
        elif t == "object":
            payload[key] = {}
        else:
            payload[key] = ""
    for key in schema.get("required", []):
        if payload.get(key) in ("", None, {}):
            payload[key] = "Not determined"
    return payload


class PromptFactoryAgent(LLMRoleAgent):
    """Mixin providing PromptFactory-based execution with schema validation
    and optional evaluator hooks."""

    _factory = PromptFactory()

    def run_with_spec(self, spec: dict[str, Any], **kwargs) -> AgentRunResult:
        prompt = self._factory.build_prompt(spec)
        schema_path = prompt.get("io_schema_ref")
        response_format = None
        schema = None
        if schema_path:
            with open(schema_path, encoding="utf-8") as fh:
                schema = json.load(fh)
            response_format = responses_json_schema_from_file(schema_path)
        user = prompt["user"]

        raw = super().act(
            prompt["system"],
            user,
            response_format=response_format,
            **(prompt.get("llm_hints") or {}),
            **kwargs,
        )
        try:
            data = json.loads(raw)
            if schema is not None:
                data = coerce_types(data, schema)
                data = strip_additional_properties(data, schema)
                jsonschema.validate(data, schema)
            valid = True
        except Exception as e:
            logger.debug("schema_validation_failed: %s", e)
            valid = False
        evaluator_fail = False
        if valid and feature_flags.EVALUATORS_ENABLED:
            if (
                prompt.get("retrieval", {}).get("enabled")
                and prompt.get("retrieval", {}).get("policy") != "NONE"
                and not data.get("sources")
            ):
                evaluator_fail = True
                logger.debug("evaluator_missing_sources")
        if valid and not evaluator_fail:
            return AgentRunResult(json.dumps(data))

        # Fallback attempt
        fallback_path = _fallback_schema_path(schema_path) if schema_path else None
        fallback_schema = schema
        if fallback_path:
            try:
                with open(fallback_path, encoding="utf-8") as fh:
                    fallback_schema = json.load(fh)
            except Exception:
                fallback_schema = schema
            response_format = responses_json_schema_from_file(fallback_path)

        fallback_spec = dict(spec)
        if fallback_path:
            fallback_spec["io_schema_ref"] = fallback_path
        fallback_spec["retrieval_policy"] = RetrievalPolicy.NONE
        fb_prompt = self._factory.build_prompt(fallback_spec)
        fb_system = (
            f"You are {spec.get('role', 'an AI assistant')}. "
            "The previous output did not meet the JSON schema. "
            "Now provide a concise result focusing on key fields in valid JSON. "
            "You may leave unknown fields empty or as 'Not determined' but must return a JSON object with the expected keys. "
            "Do not include citations or sources."
        )
        fb_user = fb_prompt.get("user", "")

        raw = super().act(
            fb_system,
            fb_user,
            response_format=response_format,
            **(fb_prompt.get("llm_hints") or {}),
            **kwargs,
        )
        try:
            data = json.loads(raw)
            if fallback_schema is not None:
                data = coerce_types(data, fallback_schema)
                data = strip_additional_properties(data, fallback_schema)
                jsonschema.validate(data, fallback_schema)
            valid = True
        except Exception as e:
            logger.debug("schema_validation_failed: %s", e)
            valid = False

        if valid:
            return AgentRunResult(json.dumps(data), fallback_used=True)

        empty = make_empty_payload(fallback_schema or {})
        return AgentRunResult(json.dumps(empty), fallback_used=True)
