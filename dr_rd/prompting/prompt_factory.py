"""Prompt factory that composes prompts from templates."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import importlib

import yaml
from jinja2 import Environment, meta

from dr_rd.examples import safety_filters
from dr_rd.prompting import example_selectors
from dr_rd.prompting.sanitizers import (
    NEUTRAL_ALIAS,
    apply_planner_neutralization,
    sanitize_planner_response,
)

from .prompt_registry import (
    RETRIEVAL_POLICY_META,
    PromptRegistry,
    RetrievalPolicy,
)
from .prompt_registry import (
    registry as default_registry,
)

CONFIG_PATH = Path("config/reporting.yaml")
CONFIG = yaml.safe_load(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
RAG_CFG = (
    yaml.safe_load(Path("config/rag.yaml").read_text()) if Path("config/rag.yaml").exists() else {}
)
PLACEHOLDER_TOKEN_RE = re.compile(r"\[(PERSON|ORG|ADDRESS|IP|DEVICE)_\d+\]")
JINJA_ENV = Environment()

_PLANNER_POSTPROCESSOR_INSTALLED = False


def _ensure_planner_postprocessor() -> None:
    global _PLANNER_POSTPROCESSOR_INSTALLED
    if _PLANNER_POSTPROCESSOR_INSTALLED:
        return

    try:
        prompt_module = importlib.import_module("core.agents.prompt_agent")
    except Exception:
        return

    original = getattr(prompt_module.PromptFactoryAgent, "run_with_spec", None)
    if original is None:
        return

    if getattr(original, "__planner_neutralizer__", False):
        _PLANNER_POSTPROCESSOR_INSTALLED = True
        return

    AgentRunResult = getattr(prompt_module, "AgentRunResult")

    def _wrapped(self, spec: dict[str, Any], **kwargs):  # type: ignore[override]
        result = original(self, spec, **kwargs)
        role = spec.get("role") if isinstance(spec, dict) else None
        if role != "Planner":
            return result

        inputs = spec.get("inputs") if isinstance(spec, dict) else None
        inputs = inputs if isinstance(inputs, dict) else {}
        alias_value = inputs.get("idea_alias") or NEUTRAL_ALIAS
        alias = alias_value if isinstance(alias_value, str) else str(alias_value)
        forbidden = _ensure_string_list(inputs.get("idea_forbidden_terms"))

        sanitized = sanitize_planner_response(str(result), forbidden, alias)
        if sanitized == str(result):
            return result

        fallback_used = getattr(result, "fallback_used", False)
        return AgentRunResult(sanitized, fallback_used=fallback_used)

    setattr(_wrapped, "__planner_neutralizer__", True)
    prompt_module.PromptFactoryAgent.run_with_spec = _wrapped  # type: ignore[assignment]
    _PLANNER_POSTPROCESSOR_INSTALLED = True


def _ensure_string_list(value: Any) -> list[str]:
    """Convert different value types into a list of non-empty strings."""

    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (list, tuple, set)):
        items = []
        for entry in value:
            if isinstance(entry, str):
                text = entry.strip()
            else:
                text = str(entry).strip()
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


def _normalize_task_scope(spec: dict[str, Any], inputs: dict[str, Any]) -> None:
    """Ensure task description and scope lists are present for prompt templates."""

    if not isinstance(inputs, dict):
        return

    role = spec.get("role")
    if role == "Reflection":
        for key in list(inputs.keys()):
            if isinstance(key, str) and key.startswith("idea"):
                inputs.pop(key, None)

    task_entry = spec.get("task")
    plan_task: dict[str, Any] | None = None
    for key in ("plan_task", "task_payload", "task_details"):
        candidate = inputs.get(key) or spec.get(key)
        if isinstance(candidate, dict):
            plan_task = candidate
            break

    description = inputs.get("task_description")
    if not description:
        if isinstance(plan_task, dict):
            description = plan_task.get("description")
        if not description and isinstance(task_entry, dict):
            description = task_entry.get("description")
        if not description:
            description = inputs.get("task") or task_entry
    if isinstance(description, (list, dict)):
        description = json.dumps(description, ensure_ascii=False, sort_keys=True)
    description_text = (description or "").strip()
    inputs["task_description"] = description_text or "Not provided"

    def _resolve_list(key: str, payload_key: str) -> list[str]:
        raw = inputs.get(key)
        if not raw and isinstance(plan_task, dict):
            raw = plan_task.get(payload_key)
        if not raw and isinstance(task_entry, dict):
            raw = task_entry.get(payload_key)
        return _ensure_string_list(raw)

    task_inputs = _resolve_list("task_inputs", "inputs")
    task_outputs = _resolve_list("task_outputs", "outputs")
    task_constraints = _resolve_list("task_constraints", "constraints")

    inputs["task_inputs"] = task_inputs or ["Not provided"]
    inputs["task_outputs"] = task_outputs or ["Not provided"]
    inputs["task_constraints"] = task_constraints or ["Not provided"]


class PromptFactory:
    """Build prompts from templates and runtime spec."""

    def __init__(self, registry: PromptRegistry | None = None) -> None:
        self.registry = registry or default_registry

    def build_prompt(self, spec: dict[str, Any]) -> dict[str, Any]:
        _ensure_planner_postprocessor()
        role = spec.get("role")
        task_key = spec.get("task_key")
        inputs = spec.get("inputs") or {}
        if not isinstance(inputs, dict):
            inputs = {}
        if isinstance(inputs.get("idea"), (dict, list)):
            inputs["idea"] = ""
        if role == "Planner":
            apply_planner_neutralization(inputs)
            inputs.setdefault("constraints_section", "")
            inputs.setdefault("risk_section", "")
        _normalize_task_scope(spec, inputs)
        template = self.registry.get(role, task_key)

        if template:
            io_schema_ref = spec.get("io_schema_ref") or template.io_schema_ref
            retrieval_policy = spec.get("retrieval_policy") or template.retrieval_policy
            evaluation_hooks = spec.get("evaluation_hooks") or template.evaluation_hooks
            provider_hints = template.provider_hints or {}
            system = template.system
            user_template = template.user_template or ""
            ast = JINJA_ENV.parse(user_template)
            placeholders = meta.find_undeclared_variables(ast) if user_template else set()
            missing = [k for k in placeholders if k not in inputs]
            if missing:
                raise ValueError(
                    "Missing required fields in PromptAgent inputs: " + ", ".join(sorted(missing))
                )
            user_prompt = (
                JINJA_ENV.from_string(user_template).render(**inputs) if user_template else ""
            )
        else:
            io_schema_ref = spec.get("io_schema_ref") or "unknown"
            retrieval_policy = spec.get("retrieval_policy") or RetrievalPolicy.NONE
            evaluation_hooks = spec.get("evaluation_hooks")
            provider_hints = {}
            system = f"You are {role}."
            user_prompt = spec.get("task", "")

        evaluation_hooks = evaluation_hooks or ["self_check_minimal"]

        system = system.strip()

        from config import feature_flags
        from dr_rd.policy.engine import load_policies

        if getattr(feature_flags, "SAFETY_ENABLED", True):
            pol = load_policies()
            summary = ", ".join(f"{k}:{v['action']}" for k, v in pol.items())
            system += f" Policies: {summary}. Sanitize or refuse."
            if getattr(feature_flags, "FILTERS_STRICT_MODE", True):
                system += " Redact PII/secrets."

        retrieval_enabled = bool(
            getattr(feature_flags, "RAG_ENABLED", False)
            or getattr(feature_flags, "ENABLE_LIVE_SEARCH", False)
        )

        policy_meta = RETRIEVAL_POLICY_META.get(
            retrieval_policy, RETRIEVAL_POLICY_META[RetrievalPolicy.NONE]
        )

        topk_map = RAG_CFG.get("topk_defaults", {})
        plan_topk = topk_map.get(retrieval_policy.name, policy_meta["top_k"])
        retrieval_plan = {
            "policy": retrieval_policy.name,
            "top_k": plan_topk,
            "domains": policy_meta["source_types"],
            "budget_hint": policy_meta["budget_hint"],
        }

        if retrieval_enabled and retrieval_policy != RetrievalPolicy.NONE:
            retrieval_text = (
                f" Retrieval policy {retrieval_policy.name}: use up to {plan_topk} items from "
                f"{', '.join(policy_meta['source_types'])}; budget {policy_meta['budget_hint']}."
                " Provide inline numbered citations and a final sources list."
            )
            system += retrieval_text

        system += (
            f" Return only JSON conforming to {io_schema_ref}. Do not include chain of thought."
        )

        inputs_blob = (user_prompt or "") + "\n" + (str(inputs) if inputs else "")
        if PLACEHOLDER_TOKEN_RE.search(inputs_blob):
            system = (
                system.rstrip()
                + "\n\nPlaceholders like [PERSON_1], [ORG_1] are aliases. Use them verbatim."
            )

        llm_hints = {"provider": "auto", "json_strict": True, "tool_use": "prefer"}
        llm_hints.update(provider_hints)
        prompt = {
            "system": system.strip(),
            "user": user_prompt.strip(),
            "io_schema_ref": io_schema_ref,
            "retrieval_plan": retrieval_plan,
            "llm_hints": llm_hints,
            "evaluation_hooks": evaluation_hooks,
        }

        if (
            getattr(feature_flags, "EXAMPLES_ENABLED", True)
            and template
            and template.example_policy
        ):
            pol = {
                "topk": CONFIG.get("EXAMPLE_TOPK_PER_ROLE", 0),
                "max_tokens": CONFIG.get("EXAMPLE_MAX_TOKENS", 0),
                "diversity_min": CONFIG.get("EXAMPLE_DIVERSITY_MIN", 0),
            }
            pol.update(template.example_policy or {})
            provider = llm_hints.get("provider", "openai")
            if provider == "auto":
                provider = "openai"
            k_hint = pol.get("topk", 0)
            max_tokens = pol.get("max_tokens", 0)
            cands = example_selectors.score_candidates(
                role, spec.get("task_sig", ""), provider, k_hint, max_tokens
            )
            policies = safety_filters.load_policies()
            cands = safety_filters.filter_and_redact(cands, policies)
            total = 0
            trimmed = []
            for c in cands:
                est = len(json.dumps(c)) // 4
                if total + est > max_tokens:
                    continue
                trimmed.append(c)
                total += est
            pack = example_selectors.pack_for_provider(
                trimmed, provider, llm_hints.get("json_mode") or llm_hints.get("json_only")
            )
            prompt["few_shots"] = pack

        return prompt
