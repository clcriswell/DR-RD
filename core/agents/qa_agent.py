"""QA specialist agent using PromptFactory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import validate

from core.llm import complete
from core.tool_router import allow_tools, call_tool
from dr_rd.prompting import PromptFactory, RetrievalPolicy


class QAAgent:
    ROLE = "QA"
    IO_SCHEMA = "dr_rd/schemas/qa_v2.json"
    ALLOWLIST = [
        "build_requirements_matrix",
        "compute_test_coverage",
        "classify_defects",
    ]

    def __init__(self, model: str) -> None:
        self.model = model
        self.factory = PromptFactory()
        allow_tools(self.ROLE, self.ALLOWLIST)

    def run(
        self,
        task: Any,
        requirements: list[str],
        tests: list[str],
        defects: list[dict],
        idea: str = "",
        context: str = "",
    ) -> Any:
        task_txt = task if isinstance(task, str) else json.dumps(task, ensure_ascii=False)
        matrix = call_tool(
            self.ROLE, "build_requirements_matrix", {"reqs": requirements, "tests": tests}
        )
        coverage = call_tool(self.ROLE, "compute_test_coverage", {"matrix": matrix})
        stats = call_tool(self.ROLE, "classify_defects", {"defects": defects})
        spec = {
            "role": self.ROLE,
            "task": task_txt,
            "inputs": {
                "idea": idea,
                "task": task_txt,
                "context": context,
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

    def _validate(self, text: Any, schema: dict, prompt: dict) -> Any:
        if isinstance(text, dict):
            data = text
        else:
            s = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
            try:
                data = json.loads(s)
                validate(data, schema)
                return data
            except Exception:
                repair_user = prompt["user"] + "\nFix to schema."
                resp = complete(
                    prompt["system"], repair_user, model=self.model, **prompt["llm_hints"]
                )
                s = (
                    resp.content
                    if isinstance(resp.content, str)
                    else json.dumps(resp.content, ensure_ascii=False)
                )
                data = json.loads(s)
                validate(data, schema)
                return data
        validate(data, schema)
        return data
