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


def execute(plan: List[Dict[str, Any]], ctx: Dict[str, Any]) -> Dict[str, Path]:
    """Write ``build_spec.md`` and ``work_plan.md`` artifacts for a run."""
    run_id = ctx.get("run_id", "latest")
    idea = ctx.get("idea", "")
    findings = ctx.get("role_to_findings", {})
    if not plan:
        placeholder = "# Work Plan\n\nNo plan could be generated.\n"
        path_plan = write_text(run_id, "work_plan", "md", placeholder)
        return {"work_plan": path_plan}

    def _arch_details() -> str:
        parts: list[str] = []
        for r in ("CTO", "Dynamic Specialist"):
            f = findings.get(r, {}).get("findings")
            if f:
                parts.append(str(f))
        return "\n".join(parts)

    def _materials_details() -> str:
        payload = findings.get("Materials Engineer", {})
        props = payload.get("properties") or []
        trade = payload.get("tradeoffs") or []
        lines: list[str] = []
        if props:
            lines.append("Properties:\n" + "\n".join(f"- {p}" for p in props))
        if trade:
            lines.append("Tradeoffs:\n" + "\n".join(f"- {t}" for t in trade))
        return "\n\n".join(lines)

    def _technical_details() -> str:
        parts: list[str] = []
        for r in ("Research Scientist", "Simulation"):
            f = findings.get(r, {}).get("findings")
            if f:
                parts.append(str(f))
        return "\n".join(parts)

    def _risks_summary() -> str:
        risks: list[str] = []
        for payload in findings.values():
            r = payload.get("risks")
            if isinstance(r, list):
                risks.extend(r)
            n = payload.get("next_steps")
            if isinstance(n, list):
                risks.extend(n)
        return "\n".join(f"- {r}" for r in risks)

    build_tpl = Path("templates/build_spec.jinja").read_text(encoding="utf-8")
    build_spec = _render(
        build_tpl,
        {
            "architecture_details": _arch_details(),
            "materials_details": _materials_details(),
            "technical_details": _technical_details(),
            "risks_summary": _risks_summary(),
        },
    )

    phase_roles = {
        "Design & Research": [
            "CTO",
            "Research Scientist",
            "Materials Engineer",
            "Simulation",
            "Dynamic Specialist",
        ],
        "Business & Compliance": [
            "Finance",
            "Marketing Analyst",
            "IP Analyst",
            "Regulatory",
            "HRM",
        ],
        "Integration & Testing": ["QA"],
    }
    phases: Dict[str, list[dict]] = {k: [] for k in phase_roles}
    phases.setdefault("Other", [])
    for t in plan:
        entry = {
            "id": t.get("id"),
            "role": t.get("role"),
            "title": t.get("title"),
            "summary": t.get("summary") or t.get("description", ""),
        }
        placed = False
        for phase, roles in phase_roles.items():
            if t.get("role") in roles:
                phases[phase].append(entry)
                placed = True
                break
        if not placed:
            phases["Other"].append(entry)

    work_tpl = Path("templates/work_plan.jinja").read_text(encoding="utf-8")
    work_plan = _render(work_tpl, {"phases": {k: v for k, v in phases.items() if v}})

    path_spec = write_text(run_id, "build_spec", "md", build_spec)
    path_plan = write_text(run_id, "work_plan", "md", work_plan)

    return {"build_spec": path_spec, "work_plan": path_plan}
