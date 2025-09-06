"""Prompt factory that composes prompts from templates."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, meta

from dr_rd.examples import safety_filters
from dr_rd.prompting import example_selectors

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


class PromptFactory:
    """Build prompts from templates and runtime spec."""

    def __init__(self, registry: PromptRegistry | None = None) -> None:
        self.registry = registry or default_registry

    def build_prompt(self, spec: dict[str, Any]) -> dict[str, Any]:
        role = spec.get("role")
        task_key = spec.get("task_key")
        inputs = spec.get("inputs") or {}
        if isinstance(inputs.get("idea"), (dict, list)):
            inputs["idea"] = ""
        template = self.registry.get(role, task_key)

        if template:
            io_schema_ref = spec.get("io_schema_ref") or template.io_schema_ref
            retrieval_policy = spec.get("retrieval_policy") or template.retrieval_policy
            evaluation_hooks = spec.get("evaluation_hooks") or template.evaluation_hooks
            provider_hints = template.provider_hints or {}
            system = template.system
            user_template = template.user_template or ""
            if user_template:
                ast = JINJA_ENV.parse(user_template)
                placeholders = meta.find_undeclared_variables(ast)
                missing = [k for k in placeholders if k not in inputs]
                if missing:
                    raise ValueError(
                        "Missing required fields in PromptAgent inputs: " + ", ".join(sorted(missing))
                    )
                user_prompt = JINJA_ENV.from_string(user_template).render(**inputs)
            else:
                placeholders = set()
                user_prompt = ""
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
