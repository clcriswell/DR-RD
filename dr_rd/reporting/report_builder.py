from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, List, Mapping, Optional, Sequence

from utils.paths import run_root
from utils.trace_export import flatten_trace_rows


def summarize_steps(trace: Sequence[Mapping[str, Any]], limit: int = 8) -> list[str]:
    """Return up to ``limit`` step summaries from earliest complete steps."""
    summaries: List[str] = []
    for step in trace:
        if step.get("status") != "complete":
            continue
        summary = (step.get("summary") or "").strip()
        if not summary:
            continue
        summaries.append(summary)
        if len(summaries) >= limit:
            break
    return summaries


def trace_table(rows: Sequence[Mapping[str, Any]]) -> str:
    """Build a compact Markdown table from flattened rows."""
    header = "| i | phase | name | status | duration_ms | tokens | cost |\n"
    header += "|---|---|---|---|---|---|---|\n"
    lines = [header]
    for r in rows:
        line = "| {i} | {phase} | {name} | {status} | {duration_ms} | {tokens} | {cost} |".format(
            i=r.get("i", ""),
            phase=r.get("phase") or "",
            name=r.get("name") or "",
            status=r.get("status") or "",
            duration_ms=r.get("duration_ms") or "",
            tokens=r.get("tokens") or "",
            cost=r.get("cost") or "",
        )
        lines.append(line)
    return "\n".join(lines)



def _format_constraints(constraints: Any) -> str:
    if constraints is None:
        return ""
    if isinstance(constraints, Mapping):
        if not constraints:
            return ""
        return "; ".join(f"{k}: {v}" for k, v in constraints.items())
    if isinstance(constraints, (list, set, tuple)):
        if not constraints:
            return ""
        return "; ".join(str(c) for c in constraints)
    return str(constraints)


def _extract_intake(meta: Mapping[str, Any]) -> tuple[str, Any]:
    intake = meta.get("intake")
    if isinstance(intake, (list, tuple)) and intake:
        idea = intake[0]
        constraints = intake[1] if len(intake) > 1 else None
        return str(idea), constraints
    idea = meta.get("idea_preview") or ""
    return str(idea), meta.get("constraints")


def build_markdown_report(
    run_id: str,
    meta: Mapping[str, Any],
    trace: Sequence[Mapping[str, Any]],
    summary_text: Optional[str],
    totals: Mapping[str, Any],
    sanitizer: Callable[[str], str] | None = None,
) -> str:
    """Assemble a human readable markdown report for a run."""

    lines: List[str] = []
    lines.append(f"# DR-RD Report — {run_id}\n")

    lines.append("## Overview")
    idea, constraints = _extract_intake(meta)
    if sanitizer:
        idea = sanitizer(idea)
    if idea:
        lines.append(f"- Idea: {idea}")
    if constraints is not None:
        formatted = _format_constraints(constraints)
        if not formatted:
            formatted = "None"
        if sanitizer:
            formatted = sanitizer(formatted)
        lines.append(f"- Constraints: {formatted}")
    mode = meta.get("mode", "")
    started = meta.get("started_at")
    completed = meta.get("completed_at")
    started_str = (
        datetime.fromtimestamp(started).isoformat() if isinstance(started, (int, float)) else ""
    )
    completed_str = (
        datetime.fromtimestamp(completed).isoformat() if isinstance(completed, (int, float)) else ""
    )
    duration = ""
    if started and completed:
        duration = str(int(completed - started)) + " s"
    if mode:
        lines.append(f"- Mode: {mode}")
    if started_str:
        lines.append(f"- Started: {started_str}")
    if completed_str:
        lines.append(f"- Completed: {completed_str}")
    if duration:
        lines.append(f"- Duration: {duration}")
    lines.append("")

    lines.append("## Key results")
    if summary_text:
        text = sanitizer(summary_text.strip()) if sanitizer else summary_text.strip()
        lines.append(text)
    else:
        for s in summarize_steps(trace):
            if sanitizer:
                s = sanitizer(s)
            lines.append(f"- {s}")
    lines.append("")

    lines.append("## Metrics")
    tokens = totals.get("tokens")
    cost = totals.get("cost")
    lines.append(f"- Steps: {len(trace)}")
    if tokens is not None:
        lines.append(f"- Tokens: {tokens}")
    if cost is not None:
        lines.append(f"- Cost: ${cost:.4f}")
    lines.append("")

    if any(k in totals for k in ["planned_tasks", "normalized_tasks", "routed_tasks", "exec_tasks"]):
        lines.append("## Task counts")
        lines.append("| planned | normalized | routed | executed |")
        lines.append("|---|---|---|---|")
        lines.append(
            "| {p} | {n} | {r} | {e} |".format(
                p=totals.get("planned_tasks", ""),
                n=totals.get("normalized_tasks", ""),
                r=totals.get("routed_tasks", ""),
                e=totals.get("exec_tasks", ""),
            )
        )
        lines.append("")

    rows = flatten_trace_rows(trace)
    lines.append("## Trace summary table")
    lines.append(trace_table(rows))
    lines.append("")

    citations: list[str] = []
    for step in trace:
        for c in step.get("citations", []) or []:
            snippet = (c.get("snippet", "") or "").replace("\n", " ")[:120]
            citations.append(f"Doc {c.get('doc_id')} — {snippet}")
    if citations:
        lines.append("## Sources")
        for c in citations:
            lines.append(f"- {c}")
        lines.append("")

    errors = [step for step in trace if step.get("status") == "error"]
    if errors:
        lines.append("## Errors")
        for e in errors:
            summary = (e.get("summary") or "").strip()
            lines.append(f"- {e.get('name', '')} — {summary}")
        lines.append("")

    root = run_root(run_id)
    artifacts: list[str] = []
    if root.exists():
        artifacts = [p.name for p in sorted(root.iterdir()) if p.is_file()]
    lines.append("## Artifacts list")
    for name in artifacts:
        lines.append(f"- {name}")
    lines.append("")

    return "\n".join(lines)


__all__ = ["build_markdown_report", "summarize_steps", "trace_table"]
