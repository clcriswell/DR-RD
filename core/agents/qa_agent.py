"""QA specialist agent using PromptFactory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from jsonschema import validate

from core.llm import complete
from core.tool_router import allow_tools, call_tool
from dr_rd.prompting import PromptFactory, RetrievalPolicy


class QAAgent:
    ROLE = "QA"
    IO_SCHEMA = "dr_rd/schemas/qa_v1.json"
    ALLOWLIST = [
        "build_requirements_matrix",
        "compute_test_coverage",
        "classify_defects",
    ]

    def __init__(self, model: str) -> None:
        self.model = model
        self.factory = PromptFactory()
        allow_tools(self.ROLE, self.ALLOWLIST)

    def run(self, task: str, requirements: List[str], tests: List[str], defects: List[dict]) -> Any:
        matrix = call_tool(
            self.ROLE, "build_requirements_matrix", {"reqs": requirements, "tests": tests}
        )
        coverage = call_tool(self.ROLE, "compute_test_coverage", {"matrix": matrix})
        stats = call_tool(self.ROLE, "classify_defects", {"defects": defects})
        spec = {
            "role": self.ROLE,
            "task": task,
            "inputs": {
                "matrix": matrix,
                "coverage": coverage,
                "defects": stats,
            },
            "io_schema_ref": self.IO_SCHEMA,
            "retrieval_policy": RetrievalPolicy.NONE,
        }
        prompt = self.factory.build_prompt(spec)
        schema = json.loads(Path(self.IO_SCHEMA).read_text())
        resp = complete(prompt["system"], prompt["user"], model=self.model, **prompt["llm_hints"])
        return self._validate(resp.content, schema, prompt)

    def _validate(self, text: str, schema: dict, prompt: dict) -> Any:
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
