from __future__ import annotations

import json
from typing import Any

import jsonschema

from config import feature_flags
from core.agents.base_agent import LLMRoleAgent
from core.llm_client import responses_json_schema_from_file
from dr_rd.prompting.prompt_factory import PromptFactory
from utils.logging import logger


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


class PromptFactoryAgent(LLMRoleAgent):
    """Mixin providing PromptFactory-based execution with schema validation
    and optional evaluator hooks."""

    _factory = PromptFactory()

    def run_with_spec(self, spec: dict[str, Any], **kwargs) -> str:
        prompt = self._factory.build_prompt(spec)
        schema_path = prompt.get("io_schema_ref")
        response_format = None
        schema = None
        if schema_path:
            with open(schema_path, encoding="utf-8") as fh:
                schema = json.load(fh)
            response_format = responses_json_schema_from_file(schema_path)
        user = prompt["user"]
        for attempt in range(2):
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
                return json.dumps(data)
            if attempt == 0:
                user = user + "\nThe previous output was invalid or missing citations. Return valid JSON only."
        return raw
