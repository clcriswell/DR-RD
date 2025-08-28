from __future__ import annotations

import json
from typing import Any, Dict

import jsonschema
from utils.logging import logger
from config import feature_flags
from dr_rd.prompting.prompt_factory import PromptFactory
from core.agents.base_agent import LLMRoleAgent


class PromptFactoryAgent(LLMRoleAgent):
    """Mixin providing PromptFactory-based execution with schema validation
    and optional evaluator hooks."""

    _factory = PromptFactory()

    def run_with_spec(self, spec: Dict[str, Any], **kwargs) -> str:
        prompt = self._factory.build_prompt(spec)
        schema_path = prompt.get("io_schema_ref")
        with open(schema_path, "r", encoding="utf-8") as fh:
            schema = json.load(fh)
        user = prompt["user"]
        for attempt in range(2):
            raw = super().act(
                prompt["system"],
                user,
                llm_hints=prompt.get("llm_hints"),
                **kwargs,
            )
            try:
                data = json.loads(raw)
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
                user = (
                    user
                    + "\nThe previous output was invalid or missing citations. Fix to schema."
                )
        return raw
