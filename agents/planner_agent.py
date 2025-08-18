from agents.base_agent import BaseAgent
import logging
import openai
from dr_rd.utils.model_router import pick_model, CallHints
from dr_rd.utils.llm_client import log_usage, llm_call
from typing import Optional
import streamlit as st

from config.feature_flags import EVALUATOR_MIN_OVERALL
from utils.json_safety import parse_json_loose

try:
    from dr_rd.knowledge.retriever import Retriever
except Exception:  # pragma: no cover
    Retriever = None  # type: ignore

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are the Creation Planner. Output ONLY valid JSON as a single array.\n"
    "[{\"role\":\"<one of: CTO, Research Scientist, Regulatory, Finance, Marketing Analyst, IP Analyst>\","\
    "\"title\":\"...\",\"description\":\"...\"}]\n"
    "Rules:\n"
    "- Return 8–12 tasks total.\n"
    "- Include AT LEAST one task for EACH of the six roles.\n"
    "- Roles MUST be exactly one of those six.\n"
    "- Titles are short imperatives; descriptions are concise and specific.\n"
    "- No prose. No backticks. JSON array only."
)


def _call_llm_json(model_id: str, messages: list, **params) -> str:
    """Call the LLM preferring JSON-mode responses."""
    base = messages + [
        {"role": "system", "content": "Respond with a single JSON array only."}
    ]
    try:
        kwargs = {"model": model_id, "messages": base, "temperature": 0}
        kwargs.update(params)
        if model_id.startswith(("gpt-4o", "gpt-4.1")):
            kwargs["response_format"] = {"type": "json_object"}
        resp = openai.chat.completions.create(**kwargs)
    except Exception:
        fallback = messages + [
            {"role": "user", "content": "Output ONLY JSON array per the rules above."}
        ]
        kwargs = {"model": model_id, "messages": fallback, "temperature": 0}
        kwargs.update(params)
        resp = openai.chat.completions.create(**kwargs)

    usage = resp.choices[0].usage if hasattr(resp.choices[0], "usage") else getattr(resp, "usage", None)
    if usage:
        log_usage(
            stage="plan",
            model=model_id,
            pt=getattr(usage, "prompt_tokens", 0),
            ct=getattr(usage, "completion_tokens", 0),
        )
    return resp.choices[0].message.content

"""Planner Agent for developing project plans."""
class PlannerAgent(BaseAgent):
    """Agent that creates a detailed project plan for the given idea."""

    def __init__(self, model, retriever: Optional[Retriever] = None):
        super().__init__(
            name="Planner",
            model=model,
            system_message="",
            user_prompt_template="",
            retriever=retriever,
        )
        self.last_raw = ""

    def run(self, idea: str, task: str, difficulty: str = "normal") -> dict:
        """Return the planner's JSON summary as a Python dict or list."""
        import json

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Project goal: {idea}\nTask: {task}",
            },
        ]

        sel = pick_model(CallHints(stage="plan", difficulty=difficulty))
        model_id = self.model if difficulty == "normal" else sel["model"]
        log.info(f"Model[plan]={model_id} params={sel['params']}")
        params = sel["params"]

        raw = _call_llm_json(model_id, messages, **params)
        self.last_raw = raw
        for _ in range(2):
            try:
                return json.loads(raw)
            except Exception:
                raw = _call_llm_json(model_id, messages, **params)
                self.last_raw = raw

        plan = parse_json_loose(raw)
        flags = st.session_state.get("final_flags", {}) if "st" in globals() else {}
        if flags.get("TEST_MODE"):
            max_domains = int(flags.get("MAX_DOMAINS", 2))
            if isinstance(plan, dict):
                plan = dict(list(sorted(plan.items(), key=lambda x: x[0])[:max_domains]))
            elif isinstance(plan, list):
                plan = plan[:max_domains]
        return plan

    def revise_plan(self, workspace_state: dict) -> list[dict]:
        """
        Given the full workspace state (tasks, results, scores),
        produce an updated list of tasks (may add, remove, reorder).
        Returns a list of dicts: [{ "role": str, "task": str, "id": str }, ...].
        """
        import json, hashlib, time
        # Build prompt
        sys = (
            "You are the R&D meta‐planner. "
            "Given the workspace state below, revise the list of tasks: "
            "- Add missing high‐level tasks, "
            "- Drop completed or irrelevant tasks, "
            "- Reorder for priority.\n"
            "Respond with JSON: { \"updated_tasks\": [ { \"role\": \"...\", \"task\": \"...\" } , ... ] }"
        )
        user = json.dumps(workspace_state, indent=2)[:8000]
        sel = pick_model(CallHints(stage="plan", difficulty="hard"))
        logging.info(f"Model[plan]={sel['model']} params={sel['params']}")
        resp = llm_call(
            openai,
            sel["model"],
            stage="plan",
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            **sel["params"],
        )
        usage = resp.choices[0].usage if hasattr(resp.choices[0], "usage") else getattr(resp, "usage", None)
        if usage:
            log_usage(
                stage="plan",
                model=sel["model"],
                pt=getattr(usage, "prompt_tokens", 0),
                ct=getattr(usage, "completion_tokens", 0),
            )
        try:
            data = resp.choices[0].message.content
            parsed = json.loads(data)
            out = []
            for t in parsed.get("updated_tasks", []):
                tid = hashlib.sha1((t["role"] + t["task"] + str(time.time())).encode()).hexdigest()[:10]
                out.append({"role": t["role"], "task": t["task"], "id": tid})
        except Exception:
            # fallback: return existing queue unchanged
            out = workspace_state.get("tasks", [])

        # Append remediation tasks if evaluation score below threshold
        scorecard = workspace_state.get("scorecard")
        remediation = []
        if scorecard and scorecard.get("overall", 1.0) < EVALUATOR_MIN_OVERALL:
            metrics = scorecard.get("metrics", {})
            for name, m in metrics.items():
                if m.get("score", 1.0) < EVALUATOR_MIN_OVERALL:
                    remediation.append({"role": "AI R&D Coordinator", "task": f"Improve {name}"})
            if not remediation:
                remediation.append({"role": "AI R&D Coordinator", "task": "Address evaluation weaknesses"})
        out.extend(remediation)
        return out
