"""Dynamic agent capable of composing role/task prompts on demand."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

from jsonschema import validate

from core.llm import complete
from core.llm_client import extract_text
from core.tool_router import allow_tools
from dr_rd.prompting import PromptFactory, RetrievalPolicy
from utils.json_safety import parse_json_loose
from utils.logging import log_dynamic_agent_failure


@dataclass
class EmptyModelOutput(Exception):
    """Raised when the model returns empty or invalid JSON."""

    role: str
    task: str
    error: str
    raw_head: str = ""
    run_id: str | None = None
    support_id: str | None = None

    def __post_init__(self) -> None:  # pragma: no cover - dataclass hook
        super().__init__(self.error)
        self.payload = {
            "role": self.role,
            "task": self.task,
            "error": self.error,
            "raw_head": self.raw_head,
        }


class DynamicAgent:
    IO_SCHEMA = "dr_rd/schemas/dynamic_agent_v1.json"

    def __init__(self, model: str) -> None:
        self.model = model
        self.factory = PromptFactory()

    def run(self, spec: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        role = spec.get("role_name", "Ad Hoc Specialist")
        task = spec.get("task_brief", "")
        context = spec.get("context", {})
        run_id = context.get("run_id")
        support_id = context.get("support_id")
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
        data = self._validate(resp.raw, schema_obj, role, task, run_id, support_id)
        return data, (schema or schema_obj)

    def _validate(
        self,
        resp: Any,
        schema: Dict[str, Any],
        role: str,
        task: str,
        run_id: str | None,
        support_id: str | None,
    ) -> Dict[str, Any]:
        if isinstance(resp, dict):
            data = resp
        else:
            text = extract_text(resp) or ""
            head = (text or "")[:256]
            if not text.strip():
                log_dynamic_agent_failure(run_id, support_id, "empty", head)
                raise EmptyModelOutput(role, task, "empty", head, run_id, support_id)
            try:
                data = parse_json_loose(text)
            except Exception:
                try:
                    data = json.loads(text)
                except Exception as e:
                    log_dynamic_agent_failure(run_id, support_id, str(e), head)
                    raise EmptyModelOutput(role, task, str(e), head, run_id, support_id) from e
        validate(data, schema)
        return data
