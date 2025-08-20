"""Planner agent with robust JSON parsing and self-repair."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError
import json

# Pydantic schema for planner output -------------------------------------------------


class Task(BaseModel):
    role: str
    title: str
    description: str


class Plan(BaseModel):
    tasks: List[Task] = Field(default_factory=list)


def _try_parse_plan(txt: str) -> Plan:
    obj = json.loads(txt)
    return Plan.model_validate(obj)


def _repair_to_json(raw_txt: str, model: str) -> str:
    """Attempt a one-shot JSON repair using a utility model."""

    repair_msgs = [
        {"role": "system", "content": "Return ONLY valid JSON for the provided content. No prose."},
        {
            "role": "user",
            "content": (
                "Fix to valid JSON matching this schema {'tasks':[{'role':str,'title':str,'description':str}]}:\n"
                + raw_txt
            ),
        },
    ]

    try:  # pragma: no cover - best effort fallback if module path changes
        from dr_rd.utils.openai_client import client  # type: ignore
    except Exception:  # pragma: no cover - fallback to core client if available
        from core.llm import client  # type: ignore

    resp = client.chat.completions.create(
        model=model,
        messages=repair_msgs,
        temperature=0.0,
        response_format={"type": "json_object"},
        max_output_tokens=800,
    )
    return resp.choices[0].message.content or "{}"


# Prompts ---------------------------------------------------------------------------

SYSTEM = "You are a Project Planner AI. Decompose the idea into role-specific tasks. Output ONLY JSON that matches {'tasks':[{'role':str,'title':str,'description':str}]}." 

USER_TMPL = "Project Idea: {idea}\nTask: Break down into role-specific tasks.\nOutput JSON only."


# Planner call ----------------------------------------------------------------------


def run_planner(idea: str, model: str, utility_model: Optional[str] = None):
    """Run the planner model and ensure a valid :class:`Plan` is returned."""

    try:  # pragma: no cover - best effort fallback if module path changes
        from dr_rd.utils.openai_client import client  # type: ignore
    except Exception:  # pragma: no cover
        from core.llm import client  # type: ignore

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER_TMPL.format(idea=idea)},
    ]

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        presence_penalty=0,
        frequency_penalty=0,
        response_format={"type": "json_object"},
        max_output_tokens=1400,
    )

    raw = resp.choices[0].message.content or "{}"
    finish = resp.choices[0].finish_reason
    usage_obj = resp.choices[0].usage if hasattr(resp.choices[0], "usage") else getattr(resp, "usage", {})
    usage = {
        "prompt_tokens": getattr(usage_obj, "prompt_tokens", 0),
        "completion_tokens": getattr(usage_obj, "completion_tokens", 0),
        "total_tokens": getattr(usage_obj, "total_tokens", 0),
    }

    try:
        plan = _try_parse_plan(raw)
    except Exception:
        repaired = _repair_to_json(raw, utility_model or model)
        plan = _try_parse_plan(repaired)

    return plan, {"finish_reason": finish, "usage": usage}


# Minimal class wrapper --------------------------------------------------------------


class PlannerAgent:
    """Lightweight wrapper maintaining backwards compatible interface."""

    def __init__(self, model: str = "o3-deep-research", repair_model: Optional[str] = "gpt-4o-mini"):
        self.model = model
        self.repair_model = repair_model
        self.system_message = SYSTEM
        self.name = "Planner"

    def run(self, idea: str, task: str, difficulty: str = "normal", roles: List[str] | None = None):
        plan, _meta = run_planner(idea, self.model, self.repair_model)
        return [t.model_dump() for t in plan.tasks]

