from __future__ import annotations

import json
import os
from typing import Any, Dict

import jsonschema

from config import feature_flags
from core.agents.base_agent import LLMRoleAgent
from core.llm_client import responses_json_schema_from_file
from dr_rd.prompting.prompt_factory import PromptFactory
from dr_rd.prompting.prompt_registry import RetrievalPolicy
from utils.logging import logger
from utils.json_fixers import attempt_auto_fix
from utils.agent_json import clean_json_payload
from core.agents.confidence import normalize_confidence


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
    """Return the relaxed fallback schema path for a given schema ref."""
    if path.endswith("_v2.json"):
        return path.replace("_v2.json", "_v2_fallback.json")
    root, ext = os.path.splitext(path)
    return f"{root}_fallback{ext}"


def make_empty_payload(schema: dict) -> dict[str, Any]:
    def _empty(prop: dict) -> Any:
        t = prop.get("type")
        if isinstance(t, list):
            if "object" in t:
                return {k: _empty(v) for k, v in (prop.get("properties") or {}).items()}
            if "array" in t:
                return []
            if "number" in t or "integer" in t:
                return 0
            return "Not determined"
        if t == "object":
            return {k: _empty(v) for k, v in (prop.get("properties") or {}).items()}
        if t == "array":
            return []
        if t in ("number", "integer"):
            return 0
        return "Not determined"

    props = schema.get("properties", {}) or {}
    return {key: _empty(prop) for key, prop in props.items()}


def _ensure_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (list, tuple, set)):
        items: list[str] = []
        for entry in value:
            text = entry.strip() if isinstance(entry, str) else str(entry).strip()
            if text:
                items.append(text)
        return items
    if isinstance(value, dict):
        cleaned = {k: v for k, v in value.items() if v not in (None, "", [], {})}
        if not cleaned:
            return []
        return [json.dumps(cleaned, ensure_ascii=False, sort_keys=True)]
    text = str(value).strip()
    return [text] if text else []


def prepare_prompt_inputs(task: Any, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    description = ""
    task_inputs: list[str] = []
    task_outputs: list[str] = []
    task_constraints: list[str] = []
    plan_task: Dict[str, Any] | None = None

    if isinstance(task, dict):
        plan_task = dict(task)
        description = str(task.get("description") or task.get("summary") or "").strip()
        if not description:
            description = str(task.get("title") or "").strip()
        task_inputs = _ensure_string_list(task.get("inputs"))
        task_outputs = _ensure_string_list(task.get("outputs"))
        task_constraints = _ensure_string_list(task.get("constraints"))
    else:
        description = str(task or "").strip()

    payload: Dict[str, Any] = {
        "task_description": description or str(task or "").strip() or "Not provided",
        "task_inputs": task_inputs,
        "task_outputs": task_outputs,
        "task_constraints": task_constraints,
    }

    if plan_task is not None:
        payload["plan_task"] = plan_task
        payload.setdefault("task_details", plan_task)

    if extra:
        payload.update(extra)

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
                data = clean_json_payload(data, schema)
                data = coerce_types(data, schema)
                data = strip_additional_properties(data, schema)
                if "confidence" in data:
                    # Convert textual descriptors like "High" to numeric scores
                    data["confidence"] = normalize_confidence(data["confidence"])
                jsonschema.validate(data, schema)
            valid = True
        except Exception as e:
            logger.debug("schema_validation_failed: %s", e)
            ok, fixed = attempt_auto_fix(raw)
            if ok:
                data = fixed
                if schema is not None:
                    if isinstance(data, dict):
                        placeholder = make_empty_payload(schema)
                        placeholder.update(data)
                        data = placeholder
                    data = clean_json_payload(data, schema)
                    data = coerce_types(data, schema)
                    data = strip_additional_properties(data, schema)
                    if "confidence" in data:
                        # Ensure confidence is numeric before validation
                        data["confidence"] = normalize_confidence(data["confidence"])
                    jsonschema.validate(data, schema)
                valid = True
                logger.info(
                    "auto_correction_applied role=%s", spec.get("role", getattr(self, "name", ""))
                )
            else:
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
        if fallback_path and os.path.exists(fallback_path):
            with open(fallback_path, encoding="utf-8") as fh:
                fallback_schema = json.load(fh)
            response_format = responses_json_schema_from_file(fallback_path)
        else:
            fallback_path = None
            response_format = (
                responses_json_schema_from_file(schema_path)
                if schema_path
                else None
            )

        fallback_spec = dict(spec)
        if fallback_path:
            fallback_spec["io_schema_ref"] = fallback_path
        fallback_spec["retrieval_policy"] = RetrievalPolicy.NONE
        fb_prompt = self._factory.build_prompt(fallback_spec)
        fb_system = (
            f"You are {spec.get('role', 'an AI assistant')}. "
            "The previous output did not meet the required JSON schema. "
            "Return a minimal JSON object matching the schema. Include at least one paragraph in the 'summary' field. "
            "Brief bullet points are acceptable for other fields, and it's fine to leave fields or sources empty."
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
                data = clean_json_payload(data, fallback_schema)
                data = coerce_types(data, fallback_schema)
                data = strip_additional_properties(data, fallback_schema)
                if "confidence" in data:
                    # Normalize textual confidence before final validation
                    data["confidence"] = normalize_confidence(data["confidence"])
                jsonschema.validate(data, fallback_schema)
            valid = True
        except Exception as e:
            logger.debug("schema_validation_failed: %s", e)
            valid = False

        if valid:
            return AgentRunResult(json.dumps(data), fallback_used=True)

        empty = make_empty_payload(fallback_schema or {})
        return AgentRunResult(json.dumps(empty), fallback_used=True)
