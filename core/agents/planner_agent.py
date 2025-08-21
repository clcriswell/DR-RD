"""Planner agent with robust JSON parsing and self-repair."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError
import json
from core.llm_client import call_openai, extract_text, llm_call
from prompts.prompts import (
    PLANNER_SYSTEM_PROMPT,
    PLANNER_USER_PROMPT_TEMPLATE,
)

# Pydantic schema for planner output -------------------------------------------------


class Task(BaseModel):
    role: str
    title: str
    description: str


class Plan(BaseModel):
    tasks: List[Task] = Field(default_factory=list)


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

    result = call_openai(
        model=model,
        messages=repair_msgs,
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    return result["text"] or "{}"


# Prompts ---------------------------------------------------------------------------

SYSTEM = PLANNER_SYSTEM_PROMPT

USER_TMPL = PLANNER_USER_PROMPT_TEMPLATE


# Planner call ----------------------------------------------------------------------


def run_planner(
    idea: str,
    model: str,
    utility_model: Optional[str] = None,
    constraints: str | None = None,
    risk_posture: str | None = None,
):
    """Run the planner model and ensure a valid :class:`Plan` is returned."""

    constraints_section = f"\nConstraints: {constraints}" if constraints else ""
    risk_section = f"\nRisk posture: {risk_posture}" if risk_posture else ""
    user_prompt = USER_TMPL.format(
        idea=idea,
        constraints_section=constraints_section,
        risk_section=risk_section,
    )
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_prompt},
    ]

    params = {
        "temperature": 0.2,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "response_format": {"type": "json_object"},
    }

    resp = llm_call(None, model, "plan", messages, **params)
    raw = extract_text(resp)
    if not isinstance(raw, str):
        try:
            raw = getattr(resp.choices[0].message, "content", raw)
        except Exception:
            raw = "{}"
    raw = raw or "{}"
    finish = None
    if getattr(resp, "choices", None):
        finish = getattr(resp.choices[0], "finish_reason", None)
        usage_obj = getattr(resp.choices[0], "usage", None)
    else:
        usage_obj = getattr(resp, "usage", None)
        if hasattr(resp, "output") and resp.output:
            finish = getattr(resp.output[0], "finish_reason", None)
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

    def __init__(self, model: str = "gpt-5", repair_model: Optional[str] = "gpt-5"):
        self.model = model
        self.repair_model = repair_model
        self.system_message = SYSTEM
        self.name = "Planner"

    def run(
        self,
        idea: str,
        task: str,
        difficulty: str = "normal",
        roles: List[str] | None = None,
        constraints: str | None = None,
        risk_posture: str | None = None,
    ):
        data, _meta = run_planner(
            idea,
            self.model,
            self.repair_model,
            constraints=constraints,
            risk_posture=risk_posture,
        )
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
        result = call_openai(
            model=self.repair_model or self.model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw = result["text"] or "{}"
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

