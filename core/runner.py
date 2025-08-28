from __future__ import annotations

"""Headless execution helper bridging Router and specialists."""

from typing import Any, Dict, Optional

from core.router import route_task


def execute_task(
    role: str,
    title: str,
    desc: str,
    inputs: Dict[str, Any],
    flag_overrides: Optional[Dict[str, Any]] = None,
    agent: Any | None = None,
) -> Dict[str, Any]:
    """Route and execute a single specialist task."""

    task = {"role": role, "title": title, "description": desc, "inputs": inputs}
    resolved_role, AgentCls, model, routed = route_task(task)
    agent = agent or AgentCls(model)
    task_text = desc or title
    fn = getattr(agent, "run", None) or getattr(agent, "__call__")
    if not callable(fn):
        raise TypeError(f"Agent {agent} has no callable interface")
    output = fn(task_text, **inputs)
    return {"role": resolved_role, "output": output}


__all__ = ["execute_task"]
