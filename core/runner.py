from __future__ import annotations

"""Headless execution helper bridging Router and specialists."""

from typing import Any, Dict, Optional

from core.router import route_task
from dr_rd.telemetry import metrics
from dr_rd.telemetry.context import telemetry_span


def execute_task(
    role: str,
    title: str,
    desc: str,
    inputs: Dict[str, Any],
    flag_overrides: Optional[Dict[str, Any]] = None,
    agent: Any | None = None,
) -> Dict[str, Any]:
    """Route and execute a single specialist task."""

    metrics.inc("runs_started")
    task = {"role": role, "title": title, "description": desc, "inputs": inputs}
    resolved_role, AgentCls, model, routed = route_task(task)
    agent = agent or AgentCls(model)
    task_text = desc or title
    fn = getattr(agent, "run", None) or getattr(agent, "__call__")
    if not callable(fn):
        metrics.inc("runs_failed")
        raise TypeError(f"Agent {agent} has no callable interface")
    with telemetry_span("run_duration", role=resolved_role):
        output = fn(task_text, **inputs)
    metrics.inc("runs_succeeded")
    return {"role": resolved_role, "output": output}


__all__ = ["execute_task"]
