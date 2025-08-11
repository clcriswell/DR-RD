from __future__ import annotations

from typing import Dict, List, Tuple

from agents.planner_agent import PlannerAgent
from core.agents.registry import build_agents, get_agent_for_task, load_mode_models
from core.synthesizer import synthesize


def run_pipeline(idea: str, mode: str = "test") -> Tuple[str, Dict[str, List[dict]], List[dict]]:
    """Run planner → specialists → synthesis pipeline."""
    models = load_mode_models(mode)
    planner_model = models.get("Planner", models.get("default", "gpt-3.5-turbo"))
    planner = PlannerAgent(planner_model)
    plan = planner.run(idea, "Decompose the project into specialist tasks")
    tasks = [{"title": task, "role": role} for role, task in plan.items()]

    agents = build_agents(mode)
    results_by_role: Dict[str, List[dict]] = {}
    context: Dict[str, List[str]] = {"idea": idea, "summaries": []}
    trace: List[dict] = []
    for t in tasks:
        agent = get_agent_for_task(t.get("title", t.get("role", "")), agents)
        result = agent.act(t.get("title", ""), context)
        results_by_role.setdefault(agent.name, []).append(result)
        summary_line = result.get("findings", [""])[0] if result.get("findings") else ""
        context["summaries"].append(summary_line)
        usage = result.get("usage", {})
        tokens = usage.get("total_tokens") or (
            usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
        )
        trace.append({"agent": agent.name, "tokens": tokens, "finding": summary_line})

    final = synthesize(idea, results_by_role, model_id=models.get("default", planner_model))
    return final, results_by_role, trace
