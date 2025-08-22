from core.agents.base_agent import BaseAgent
from core.model_router import pick_model, CallHints
from core.llm_client import log_usage, call_openai
from typing import Optional, Dict, Any
import json
import re
from prompts.prompts import (
    IP_ANALYST_SYSTEM_PROMPT,
    IP_ANALYST_USER_PROMPT_TEMPLATE,
)


class IPAnalystAgent(BaseAgent):
    """Agent for prior art scans, novelty checks and IP strategy."""

    def __init__(self, model: str, retriever: Optional[Any] = None):
        super().__init__(
            name="IP Analyst",
            model=model,
            system_message=IP_ANALYST_SYSTEM_PROMPT,
            user_prompt_template=IP_ANALYST_USER_PROMPT_TEMPLATE,
            retriever=retriever,
        )

    def act(self, idea: str, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prompt = self.user_prompt_template.format(idea=idea, task=task)
        prompt = self._augment_prompt(prompt, idea, task)
        sel = pick_model(CallHints(stage="exec"))
        result = call_openai(
            model=sel["model"],
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ],
            **sel["params"],
        )
        resp = result["raw"]
        usage = getattr(resp, "usage", None)
        if usage is None and getattr(resp, "choices", None):
            usage = getattr(resp.choices[0], "usage", None)
        if usage:
            log_usage(
                stage="exec",
                model=sel["model"],
                pt=getattr(usage, "prompt_tokens", 0),
                ct=getattr(usage, "completion_tokens", 0),
            )
        raw = (result["text"] or "").strip()
        data: Dict[str, Any]
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception:
                    data = {
                        "role": self.name,
                        "task": task,
                        "findings": [raw],
                        "risks": [],
                        "next_steps": [],
                    }
            else:
                data = {
                    "role": self.name,
                    "task": task,
                    "findings": [raw],
                    "risks": [],
                    "next_steps": [],
                }
        data.setdefault("role", self.name)
        data.setdefault("task", task)
        data.setdefault("findings", [])
        data.setdefault("risks", [])
        data.setdefault("next_steps", [])
        if self._sources:
            data.setdefault("sources", self._sources)
        return data
