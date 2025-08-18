from agents.base_agent import BaseAgent
import logging
import openai
from dr_rd.utils.model_router import pick_model, CallHints
from dr_rd.utils.llm_client import llm_call, log_usage
from typing import Optional
import streamlit as st

from config.feature_flags import EVALUATOR_MIN_OVERALL

try:
    from dr_rd.knowledge.retriever import Retriever
except Exception:  # pragma: no cover
    Retriever = None  # type: ignore

"""Planner Agent for developing project plans."""
class PlannerAgent(BaseAgent):
    """Agent that creates a detailed project plan for the given idea."""

    def __init__(self, model, retriever: Optional[Retriever] = None):
        super().__init__(
            name="Planner",
            model=model,
            system_message=(
                "You are an expert project planner specializing in turning ideas into actionable plans."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\n"
                "As the Planner, your task is {task}.\n\n"
                "Return **only** a JSON object mapping each relevant team role (from the list below) to one or two succinct tasks. "
                "Include a role only if it would reasonably contribute to this project:\n"
                "  - Mechanical Systems Lead\n"
                "  - Materials & Process Engineer\n"
                "  - Chemical & Surface Science Specialist\n"
                "  - Quantum Optics Physicist\n"
                "  - Nonlinear Optics / Crystal Engineer\n"
                "  - Optical Systems Engineer\n"
                "  - Mechanical & Precision-Motion Engineer\n"
                "  - Photonics Electronics Engineer\n"
                "  - Electronics & Embedded Controls Engineer\n"
                "  - Software / Image-Processing Specialist\n"
                "  - Fluorescence / Biological Sample Expert\n"
                "  - Systems Integration & Validation Engineer\n"
                "  - Data Scientist / Analytics Engineer\n"
                "  - Regulatory & Compliance Lead\n"
                "  - Prototyping & Test Lab Manager\n"
                "  - Project Manager / Principal Investigator\n"
                "  - Product Manager / Translational Lead\n"
                "  - AI R&D Coordinator\n"
                "  - Marketing Analyst\n"
                "  - IP Analyst\n\n"
                "Only include roles that are relevant, and do not include any roles outside this list. "
                "Use each role name exactly as given above as JSON keys, and provide a brief task description for each selected role."
            ),
            retriever=retriever,
        )

    def run(self, idea: str, task: str, difficulty: str = "normal") -> dict:
        """Return the planner's JSON summary as a Python dict."""
        import json

        prompt = self.user_prompt_template.format(idea=idea, task=task)
        prompt = self._augment_prompt(prompt, idea, task)

        kwargs = {
            "messages": [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ]
        }

        sel = pick_model(CallHints(stage="plan", difficulty=difficulty))
        model_id = self.model if difficulty == "normal" else sel["model"]
        logging.info(f"Model[plan]={model_id} params={sel['params']}")
        if model_id.startswith(("gpt-4o", "gpt-4.1")):
            kwargs["response_format"] = {"type": "json_object"}
        kwargs.update(sel["params"])
        response = llm_call(openai, model_id, stage="plan", **kwargs)
        usage = response.choices[0].usage if hasattr(response.choices[0], "usage") else getattr(response, "usage", None)
        if usage:
            log_usage(
                stage="plan",
                model=model_id,
                pt=getattr(usage, "prompt_tokens", 0),
                ct=getattr(usage, "completion_tokens", 0),
            )
        raw_text = response.choices[0].message.content
        logging.debug("Planner raw response: %s", raw_text)
        try:
            plan = json.loads(raw_text)
            flags = st.session_state.get("final_flags", {}) if "st" in globals() else {}
            if flags.get("TEST_MODE"):
                max_domains = int(flags.get("MAX_DOMAINS", 2))
                plan = dict(sorted(plan.items(), key=lambda x: x[0])[:max_domains])
            return plan
        except json.JSONDecodeError as e:
            raise ValueError(f"Planner returned invalid JSON: {raw_text}") from e

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
