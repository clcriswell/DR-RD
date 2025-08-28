"""Prompt factory that composes prompts from templates."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .prompt_registry import (
    PromptRegistry,
    RetrievalPolicy,
    RETRIEVAL_POLICY_META,
    registry as default_registry,
)


class PromptFactory:
    """Build prompts from templates and runtime spec."""

    def __init__(self, registry: Optional[PromptRegistry] = None) -> None:
        self.registry = registry or default_registry

    def build_prompt(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        role = spec.get("role")
        task_key = spec.get("task_key")
        inputs = spec.get("inputs") or {}
        template = self.registry.get(role, task_key)

        if template:
            io_schema_ref = spec.get("io_schema_ref") or template.io_schema_ref
            retrieval_policy = spec.get("retrieval_policy") or template.retrieval_policy
            evaluation_hooks = spec.get("evaluation_hooks") or template.evaluation_hooks
            provider_hints = template.provider_hints or {}
            system = template.system
            user_prompt = template.user_template.format(**inputs)
        else:
            io_schema_ref = spec.get("io_schema_ref") or "unknown"
            retrieval_policy = spec.get("retrieval_policy") or RetrievalPolicy.NONE
            evaluation_hooks = spec.get("evaluation_hooks")
            provider_hints = {}
            system = f"You are {role}."
            user_prompt = spec.get("task", "")

        evaluation_hooks = evaluation_hooks or ["self_check_minimal"]

        guardrail = (
            f" You must reply only with a JSON object matching the schema: {io_schema_ref}."
        )
        system = system.strip() + guardrail

        from config import feature_flags

        retrieval_enabled = bool(
            getattr(feature_flags, "RAG_ENABLED", False)
            or getattr(feature_flags, "ENABLE_LIVE_SEARCH", False)
        )

        meta = RETRIEVAL_POLICY_META.get(
            retrieval_policy, RETRIEVAL_POLICY_META[RetrievalPolicy.NONE]
        )

        retrieval_dict = {
            "policy": retrieval_policy.name,
            "top_k": meta["top_k"],
            "source_types": meta["source_types"],
            "budget_hint": meta["budget_hint"],
            "enabled": retrieval_enabled,
        }

        if retrieval_enabled and retrieval_policy != RetrievalPolicy.NONE:
            retrieval_text = (
                f" Retrieval policy {retrieval_policy.name}: use up to {meta['top_k']} items from "
                f"{', '.join(meta['source_types'])}; budget {meta['budget_hint']}."
                " Provide inline numbered citations and a final sources list."
            )
            system += retrieval_text

        llm_hints = {"provider": "auto", "json_strict": True, "tool_use": "prefer"}
        llm_hints.update(provider_hints)

        return {
            "system": system.strip(),
            "user": user_prompt.strip(),
            "io_schema_ref": io_schema_ref,
            "retrieval": retrieval_dict,
            "llm_hints": llm_hints,
            "evaluation_hooks": evaluation_hooks,
        }
