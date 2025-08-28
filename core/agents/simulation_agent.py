from __future__ import annotations

import json
from typing import Any, Dict

from core.agents.base_agent import LLMRoleAgent
from dr_rd.simulation import sim_core
from dr_rd.simulation.interfaces import SimulationSpec


def determine_sim_type(role: str, design_spec: str) -> str:
    role = role.lower()
    if "mechanical" in role or "motion" in role:
        return "mechanical"
    if "material" in role:
        return "materials"
    if "finance" in role:
        return "finance"
    text = design_spec.lower()
    if "monte" in text or "npv" in text:
        return "finance"
    return ""


class SimulationAgent(LLMRoleAgent):
    """Agent that delegates to registered simulators."""

    def run(self, task: Dict[str, Any], **kwargs) -> str:
        domain = task.get("domain", "")
        spec = SimulationSpec(
            id=str(task.get("id", "sim")),
            domain=domain,
            inputs=task.get("inputs", {}),
            budget_hint=task.get("budget_hint"),
            seed=task.get("seed"),
            notes=task.get("notes"),
        )
        budget = task.get("budget", {})
        result = sim_core.run(domain, spec, budget)
        payload = {
            "role": "Simulation",
            "task": task.get("task", ""),
            "domain": domain,
            "inputs": spec.inputs,
            "findings": result.findings,
            "metrics": result.metrics,
            "artifacts": result.artifacts or [],
            "sources": result.sources or [],
            "cost_summary": result.cost_summary or {},
            "spans": result.spans or [],
        }
        return json.dumps(payload)
