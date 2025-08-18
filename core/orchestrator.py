from __future__ import annotations

from typing import Dict, List, Tuple

import logging
import streamlit as st
from agents.planner_agent import PlannerAgent
from core.agents.registry import build_agents, choose_agent_for_task, load_mode_models
from core.synthesizer import synthesize

logger = logging.getLogger(__name__)


def run_pipeline(
    idea: str, mode: str = "test",
) -> Tuple[str, Dict[str, List[dict]], List[dict]]:
    """Run iterative planner → specialists → synthesis pipeline."""
    models = load_mode_models(mode)
    planner_model = models.get("Planner", models.get("default", "gpt-3.5-turbo"))
    planner = PlannerAgent(planner_model)
    agents = build_agents(mode)

    max_loops = int(st.session_state.get("MODE_CFG", {}).get("max_loops", 5))
    cycle = 0
    task_queue: List[dict] = []
    results_by_role: Dict[str, List[dict]] = {}
    trace: List[dict] = []
    context: Dict[str, List[str]] = {"idea": idea, "summaries": []}

    plan = planner.run(idea, "Decompose the project into specialist tasks")
    task_queue.extend({"role": r, "title": t} for r, t in plan.items())

    while True:
        if not task_queue:
            followups = planner.revise_plan({"idea": idea, "results": results_by_role})
            if not followups:
                break
            task_queue.extend({"role": t.get("role"), "title": t.get("task")} for t in followups)
        cycle += 1
        batch = list(task_queue)
        task_queue.clear()
        for task in batch:
            agent, routed_role = choose_agent_for_task(
                task.get("role"), task.get("title", ""), agents
            )
            logger.info(
                "Dispatch '%s' planned_role=%s -> routed_role=%s",
                task.get("title"),
                task.get("role"),
                routed_role,
            )
            result = agent.act(idea, task.get("title", ""), context)
            results_by_role.setdefault(routed_role, []).append(result)
            summary_line = result.get("findings", [""])[0] if result.get("findings") else ""
            context["summaries"].append(summary_line)
            usage = result.get("usage", {})
            tokens = usage.get("total_tokens") or (
                usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
            )
            trace.append({"agent": routed_role, "tokens": tokens, "finding": summary_line})
        logger.info(
            "Cycle %s — executed %s tasks; queue=%s", cycle, len(batch), len(task_queue)
        )
        if cycle >= max_loops and not task_queue:
            break

    final = synthesize(idea, results_by_role, model_id=models.get("synth", planner_model))
    return final, results_by_role, trace
