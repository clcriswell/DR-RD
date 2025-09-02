"""Executor orchestrator that emits build artifacts."""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

from utils.paths import write_text


def _render(template: str, context: Dict[str, Any]) -> str:
    try:
        from jinja2 import Template

        return Template(template).render(**context)
    except Exception:
        return template.format(**context)


DEFAULT_BUILD_SPEC = "# Build Spec\n\nGenerated for: {idea}\n"
DEFAULT_WORK_PLAN = "# Work Plan\n\nTasks:\n{tasks}\n"


def execute(plan: List[Dict[str, Any]], ctx: Dict[str, Any]) -> Dict[str, Path]:
    """Write ``build_spec.md`` and ``work_plan.md`` artifacts for a run."""
    run_id = ctx.get("run_id", "latest")
    idea = ctx.get("idea", "")
    tasks_md = "\n".join(f"- {t.get('title','')}" for t in plan)
    context = {"idea": idea, "tasks": tasks_md}

    build_spec = _render(DEFAULT_BUILD_SPEC, context)
    work_plan = _render(DEFAULT_WORK_PLAN, context)

    path_spec = write_text(run_id, "build_spec", "md", build_spec)
    path_plan = write_text(run_id, "work_plan", "md", work_plan)

    return {"build_spec": path_spec, "work_plan": path_plan}
