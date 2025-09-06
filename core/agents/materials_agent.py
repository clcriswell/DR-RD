"""Materials specialist agent using PromptFactory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import validate

from core.llm import complete
from core.tool_router import allow_tools, call_tool
from dr_rd.prompting import PromptFactory, RetrievalPolicy
from core.agents.prompt_agent import strip_additional_properties


class MaterialsAgent:
    ROLE = "Materials"
    IO_SCHEMA = "dr_rd/schemas/materials_v1.json"
    ALLOWLIST = ["lookup_materials"]

    def __init__(self, model: str) -> None:
        self.model = model
        self.factory = PromptFactory()
        allow_tools(self.ROLE, self.ALLOWLIST)

    def run(self, task: str, query: str) -> Any:
        materials = call_tool(self.ROLE, "lookup_materials", {"query": query})
        spec = {
            "role": self.ROLE,
            "task": task,
            "inputs": {"query": query, "materials": materials},
            "io_schema_ref": self.IO_SCHEMA,
            "retrieval_policy": RetrievalPolicy.LIGHT,
        }
        prompt = self.factory.build_prompt(spec)
        schema = json.loads(Path(self.IO_SCHEMA).read_text())
        resp = complete(prompt["system"], prompt["user"], model=self.model, **prompt["llm_hints"])
        data = self._validate(resp.content, schema, prompt)
        return data

    def _validate(self, text: str, schema: dict, prompt: dict) -> Any:
        try:
            data = json.loads(text)
            data = strip_additional_properties(data, schema)
            validate(data, schema)
            return data
        except Exception:
            repair_user = (
                prompt["user"]
                + "\nFix to schema. Only include the JSON keys defined in the schema. Do not add any other fields. Ensure 'properties' is an array of objects with fields name, property, value, units, source."
            )
            resp = complete(
                prompt["system"], repair_user, model=self.model, **prompt["llm_hints"]
            )
            data = json.loads(resp.content)
            data = strip_additional_properties(data, schema)
            validate(data, schema)
            return data
