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


def llm_call(**kwargs):
    """Wrapper around the OpenAI chat completions API for easy patching in tests."""

    # If the compatibility shim has been patched, delegate to it.
    try:  # pragma: no cover - avoids circular import during normal runtime
        from agents import planner_agent as compat  # type: ignore
        ext = getattr(compat, "llm_call", None)
        if ext is not None and ext is not llm_call:
            return ext(**kwargs)
    except Exception:  # pragma: no cover - ignore if import fails
        pass

    try:  # pragma: no cover - best effort fallback if module path changes
        from dr_rd.utils.openai_client import client  # type: ignore
    except Exception:  # pragma: no cover - fallback to core client if available
        from core.llm import client  # type: ignore

    return client.chat.completions.create(**kwargs)


def _try_parse_plan(txt: str) -> dict:
    return json.loads(txt)


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

    resp = llm_call(
        model=model,
        messages=repair_msgs,
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or "{}"


# Prompts ---------------------------------------------------------------------------

SYSTEM = "You are a Project Planner AI. Decompose the idea into role-specific tasks. Output ONLY JSON that matches {'tasks':[{'role':str,'title':str,'description':str}]}." 

USER_TMPL = "Project Idea: {idea}\nTask: Break down into role-specific tasks.\nOutput JSON only."


# Planner call ----------------------------------------------------------------------


def run_planner(idea: str, model: str, utility_model: Optional[str] = None):
    """Run the planner model and ensure a valid :class:`Plan` is returned."""

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER_TMPL.format(idea=idea)},
    ]

    params = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "presence_penalty": 0,
        "frequency_penalty": 0,
    }
    if not model.startswith("gpt-4") or model.startswith("gpt-4o"):
        params["response_format"] = {"type": "json_object"}

    resp = llm_call(**params)

    raw = resp.choices[0].message.content or "{}"
    finish = resp.choices[0].finish_reason
    usage_obj = resp.choices[0].usage if hasattr(resp.choices[0], "usage") else getattr(resp, "usage", {})
    usage = {
        "prompt_tokens": getattr(usage_obj, "prompt_tokens", 0),
        "completion_tokens": getattr(usage_obj, "completion_tokens", 0),
        "total_tokens": getattr(usage_obj, "total_tokens", 0),
    }

    try:
        data = _try_parse_plan(raw)
    except Exception:
        fixed = raw.rsplit(",", 1)[0] + "}"
        try:
            data = _try_parse_plan(fixed)
        except Exception:
            repaired = _repair_to_json(raw, utility_model or model)
            data = _try_parse_plan(repaired)

    return data, {"finish_reason": finish, "usage": usage}


# Minimal class wrapper --------------------------------------------------------------


class PlannerAgent:
    """Lightweight wrapper maintaining backwards compatible interface."""

    def __init__(self, model: str = "o3-deep-research", repair_model: Optional[str] = "o3-deep-research"):
        self.model = model
        self.repair_model = repair_model
        self.system_message = SYSTEM
        self.name = "Planner"

    def run(self, idea: str, task: str, difficulty: str = "normal", roles: List[str] | None = None):
        data, _meta = run_planner(idea, self.model, self.repair_model)
        return data

    def revise_plan(self, workspace: dict) -> List[dict]:
        from config.feature_flags import EVALUATOR_MIN_OVERALL

        score = workspace.get("scorecard", {}).get("overall", 1.0)
        if score >= EVALUATOR_MIN_OVERALL:
            return workspace.get("tasks", [])

        messages = [
            {
                "role": "system",
                "content": "Return JSON with key 'updated_tasks' listing remediation tasks.",
            },
            {"role": "user", "content": json.dumps(workspace)},
        ]
        resp = llm_call(
            model=self.repair_model or self.model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        try:
            data = json.loads(raw)
        except Exception:
            data = {}
        tasks = data.get("updated_tasks") or []
        if not tasks:
            tasks = [
                {
                    "role": "Project Manager",
                    "task": "Improve plan based on evaluator feedback",
                    "description": "Address weaknesses identified in the scorecard.",
                }
            ]
        return tasks

