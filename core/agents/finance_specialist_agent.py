"""Finance specialist agent using PromptFactory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import validate

from core.llm import complete
from core.tool_router import allow_tools, call_tool
from dr_rd.prompting import PromptFactory, RetrievalPolicy


class FinanceSpecialistAgent:
    ROLE = "Finance Specialist"
    IO_SCHEMA = "dr_rd/schemas/finance_v2.json"
    ALLOWLIST = ["calc_unit_economics", "npv", "monte_carlo"]

    def __init__(self, model: str) -> None:
        self.model = model
        self.factory = PromptFactory()
        allow_tools(self.ROLE, self.ALLOWLIST)

    def run(self, task: str, line_items: list[dict], cash_flows: list[float], params: dict) -> Any:
        econ = call_tool(self.ROLE, "calc_unit_economics", {"line_items": line_items})
        npv_val = call_tool(self.ROLE, "npv", {"cash_flows": cash_flows, "discount_rate": 0.1})
        sim = call_tool(self.ROLE, "monte_carlo", {"params": params, "trials": 100})
        spec = {
            "role": self.ROLE,
            "task": task,
            "inputs": {"economics": econ, "npv": npv_val, "sim": sim},
            "io_schema_ref": self.IO_SCHEMA,
            "retrieval_policy": RetrievalPolicy.NONE,
            "evaluation_hooks": ["compartment_check", "self_check_minimal"],
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
