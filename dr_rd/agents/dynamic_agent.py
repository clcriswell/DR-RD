"""Dynamic agent capable of composing role/task prompts on demand."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from jsonschema import validate

from core.llm import complete
from core.tool_router import allow_tools
from dr_rd.prompting import PromptFactory, RetrievalPolicy


class DynamicAgent:
    IO_SCHEMA = "dr_rd/schemas/dynamic_agent_v1.json"

    def __init__(self, model: str) -> None:
        self.model = model
        self.factory = PromptFactory()

    def run(self, spec: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        role = spec.get("role_name", "Ad Hoc Specialist")
        task = spec.get("task_brief", "")
        io_schema_ref = spec.get("io_schema_ref")
        schema: Dict[str, Any] | None = None
        if not io_schema_ref:
            draft = spec.get("schema_draft", {"type": "object"})
            schema = {"$schema": "http://json-schema.org/draft-07/schema#"}
            schema.update(draft)
        allow_tools(role, spec.get("tool_allowlist", []))
        prompt_spec = {
            "role": role,
            "task": task,
            "io_schema_ref": self.IO_SCHEMA,
            "retrieval_policy": spec.get("retrieval_policy", RetrievalPolicy.NONE),
        }
        prompt = self.factory.build_prompt(prompt_spec)
        schema_obj = json.loads(Path(self.IO_SCHEMA).read_text())
        resp = complete(prompt["system"], prompt["user"], model=self.model, **prompt["llm_hints"])
        data = self._validate(resp.content, schema_obj, prompt)
        return data, (schema or schema_obj)

    def _validate(
        self, text: str, schema: Dict[str, Any], prompt: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            data = json.loads(text)
            validate(data, schema)
            return data
        except Exception:
            repair_user = prompt["user"] + "\nFix to schema."
            resp = complete(prompt["system"], repair_user, model=self.model, **prompt["llm_hints"])
            data = json.loads(resp.content)
            validate(data, schema)
            return data
