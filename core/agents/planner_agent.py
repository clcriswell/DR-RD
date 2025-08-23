"""Planner agent with robust JSON parsing and self-repair."""

from __future__ import annotations

import json
import logging
import os
from typing import List, Optional

from pydantic import BaseModel, Field

from config.feature_flags import (
    ENABLE_LIVE_SEARCH,
    LIVE_SEARCH_BACKEND,
    LIVE_SEARCH_MAX_CALLS,
    LIVE_SEARCH_SUMMARY_TOKENS,
    RAG_ENABLED,
    RAG_TOPK,
    VECTOR_INDEX_PRESENT,
)
from core.llm_client import (
    _strip_code_fences,
    call_openai,
    extract_planner_payload,
    llm_call,
)
from dr_rd.retrieval.context import fetch_context
from core.retrieval import budget as rbudget
from prompts.prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

# Pydantic schema for planner output -------------------------------------------------


class Task(BaseModel):
    role: str
    title: str
    description: str


class Plan(BaseModel):
    tasks: List[Task] = Field(default_factory=list)


def _try_parse_plan(txt: str) -> dict:
    if not txt or not txt.strip():
        raise ValueError("Empty planner payload text")
    return json.loads(_strip_code_fences(txt))


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


def _json_repair_safe(raw_txt: str, model: str) -> str:
    try:
        return _repair_to_json(raw_txt, model)
    except Exception:
        return ""


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
    vector_available = VECTOR_INDEX_PRESENT
    cfg = {
        "rag_enabled": RAG_ENABLED and vector_available,
        "rag_top_k": RAG_TOPK,
        "live_search_enabled": ENABLE_LIVE_SEARCH,
        "live_search_backend": LIVE_SEARCH_BACKEND,
        "live_search_summary_tokens": LIVE_SEARCH_SUMMARY_TOKENS,
        "vector_index_present": vector_available,
        "live_search_max_calls": LIVE_SEARCH_MAX_CALLS,
    }
    ctx = fetch_context(cfg, idea, "Planner", "plan")
    trace = ctx["trace"]
    logger.info(
        "RetrievalTrace agent=Planner task_id=plan rag_hits=%d web_used=%s backend=%s sources=%d reason=%s",
        trace.get("rag_hits", 0),
        str(trace.get("web_used", False)).lower(),
        trace.get("backend", "none"),
        trace.get("sources", 0),
        trace.get("reason", "ok"),
    )
    if ctx.get("rag_snippets"):
        user_prompt += "\n\n# RAG Knowledge\n" + "\n".join(ctx["rag_snippets"])
    if ctx.get("web_results"):
        user_prompt += "\n\n# Web Search Results\n"
        for res in ctx["web_results"]:
            title = res.get("title", "")
            snippet = res.get("snippet", "")
            url = res.get("url", "")
            user_prompt += f"- {title}: {snippet} ({url})\n"
        user_prompt += "\nIf you use Web Search Results, include a sources array in your JSON with short titles or URLs."
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
    planner_seed = os.getenv("DRRD_PLANNER_SEED")
    if planner_seed:
        try:
            params["seed"] = int(planner_seed)
        except ValueError:
            pass
        use_chat = os.getenv("DRRD_USE_CHAT_FOR_SEEDED", "false").lower() in (
            "1",
            "true",
            "yes",
        )
        if not use_chat:
            logger.info("Planner seed provided but Responses API is in use; seed will be ignored.")

    resp = llm_call(None, model, "plan", messages, **params)
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

    used = rbudget.RETRIEVAL_BUDGET.used if rbudget.RETRIEVAL_BUDGET else 0
    cap = rbudget.RETRIEVAL_BUDGET.max_calls if rbudget.RETRIEVAL_BUDGET else 0
    logger.info("RetrievalBudget web_search_calls=%d/%d", used, cap)

    try:
        data = extract_planner_payload(resp)
    except Exception:
        raw = getattr(resp, "output_text", "") or ""
        repaired = _json_repair_safe(raw, utility_model or model)
        if repaired and repaired.strip():
            data = json.loads(repaired)
        else:
            raise

    return data, {"finish_reason": finish, "usage": usage}


# Minimal class wrapper --------------------------------------------------------------


class PlannerAgent:
    """Lightweight wrapper maintaining backwards compatible interface."""

    def __init__(self, model: str = "gpt-4.1-mini", repair_model: Optional[str] = None):
        self.model = model
        self.repair_model = repair_model or model
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

    def act(
        self,
        idea: str,
        task: str,
        difficulty: str = "normal",
        roles: List[str] | None = None,
        constraints: str | None = None,
        risk_posture: str | None = None,
    ):
        return self.run(
            idea,
            task,
            difficulty=difficulty,
            roles=roles,
            constraints=constraints,
            risk_posture=risk_posture,
        )

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
