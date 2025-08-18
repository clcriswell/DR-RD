from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
from abc import ABC

import openai
from dr_rd.utils.llm_client import llm_call


@dataclass
class Agent(ABC):
    """Simple specialist agent interface."""

    name: str
    role: str
    model_id: str
    system_prompt: str = ""

    def _call_openai(self, idea: str, task: str, context: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt or f"You are {self.role}."},
            {
                "role": "user",
                "content": (
                    f"Project Idea: {idea}\nTask: {task}\nContext: {context}\n"
                    "Provide your analysis in Markdown followed by a JSON block with keys: role, task, findings, risks, next_steps, sources."
                ),
            },
        ]
        resp = llm_call(openai, self.model_id, stage="exec", messages=messages)
        return resp.choices[0].message.content

    def act(self, idea: str, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the agent for a given task and shared context."""
        raw = self._call_openai(idea, task, json.dumps(context or {}))
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {
                "role": self.role,
                "task": task,
                "findings": [raw],
                "risks": [],
                "next_steps": [],
                "sources": [],
            }
        # Attach usage from session log if available
        usage_log = getattr(__import__("streamlit"), "session_state", {}).get("usage_log", [])
        if usage_log:
            last = usage_log[-1]
            pt = last.get("pt", 0)
            ct = last.get("ct", 0)
            try:
                pt = int(pt)
            except Exception:
                pt = 0
            try:
                ct = int(ct)
            except Exception:
                ct = 0
            data["usage"] = {
                "prompt_tokens": pt,
                "completion_tokens": ct,
                "total_tokens": pt + ct,
            }
        return data
