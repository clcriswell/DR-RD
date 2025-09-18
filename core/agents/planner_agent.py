from __future__ import annotations

from typing import Any
import json

from core.agents.prompt_agent import PromptFactoryAgent, prepare_prompt_inputs
from dr_rd.prompting.prompt_registry import RetrievalPolicy
from core.llm import select_model
from config import feature_flags
from core.safety_gate import preflight


class PlannerAgent(PromptFactoryAgent):
    def act(self, idea: str, task: Any = None, **kwargs) -> str:
        text = str(task or "")
        inputs = prepare_prompt_inputs(task, idea=idea)
        spec = {
            "role": "Planner",
            "task": text,
            "inputs": inputs,
            "io_schema_ref": "dr_rd/schemas/planner_v1.json",
            "retrieval_policy": RetrievalPolicy.LIGHT,
            "capabilities": "task planning",
            "evaluation_hooks": ["compartment_check", "self_check_minimal"],
        }
        raw = super().run_with_spec(spec, **kwargs)
        try:
            data = json.loads(raw)
            text = json.dumps(data).lower()
            if any(k in text for k in ["simulate", "model", "digital twin"]):
                data.setdefault("hints", {})["simulation_domain"] = "generic"
            if feature_flags.POLICY_AWARE_PLANNING:
                risks = preflight(str(task))
                data["risk_register"] = [
                    {"class": r, "likelihood": "low", "mitigation": "sanitize"}
                    for r in risks
                ]
                data["policy_flags"] = {"policy_aware": True}
            return json.dumps(data)
        except Exception:
            return raw

    def run(self, idea: str, task: Any, **kwargs) -> str:
        return self.act(idea, task, **kwargs)


def run_planner(idea: str, task: Any, model: str | None = None) -> str:
    agent = PlannerAgent(model or select_model("agent", agent_name="Planner"))
    return agent.run(idea, task)
