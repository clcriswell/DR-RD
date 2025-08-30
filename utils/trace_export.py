from __future__ import annotations

import csv
import io
import json
from collections import OrderedDict
from typing import Any, Dict, List, Sequence

from .paths import write_bytes

Row = List[Any]


def _safe_summary(text: str | None, max_len: int = 80) -> str:
    text = text or ""
    return text[:max_len]


def to_json(trace: Sequence[Dict[str, Any]]) -> bytes:
    """Return the trace as JSON bytes."""
    return json.dumps(list(trace), ensure_ascii=False, indent=2).encode("utf-8")


def to_csv(trace: Sequence[Dict[str, Any]], run_id: str | None = None) -> bytes:
    """Return a CSV summary of the trace."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "run_id",
        "phase",
        "step_index",
        "name",
        "status",
        "duration_ms",
        "tokens",
        "cost",
        "summary_80chars",
    ])
    for idx, step in enumerate(trace, 1):
        writer.writerow([
            run_id,
            step.get("phase"),
            idx,
            step.get("name"),
            step.get("status"),
            step.get("duration_ms"),
            step.get("tokens"),
            step.get("cost"),
            _safe_summary(step.get("summary")),
        ])
    return output.getvalue().encode("utf-8")


def to_markdown(trace: Sequence[Dict[str, Any]], run_id: str | None = None) -> bytes:
    """Return a human readable Markdown report of the trace."""
    phases: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict()
    for step in trace:
        phase = (step.get("phase") or "unknown").lower()
        phases.setdefault(phase, []).append(step)

    lines: List[str] = []
    title = f"Trace {run_id}" if run_id else "Trace"
    lines.append(f"# {title}\n")
    for phase, steps in phases.items():
        lines.append(f"## {phase.capitalize()}\n")
        total = len(steps)
        for i, step in enumerate(steps, 1):
            status = step.get("status")
            badge = {"complete": "✅", "error": "⚠️", "running": "⏳"}.get(status, "")
            header = f"### Step {i}/{total} — {step.get('name', '')} {badge}".rstrip()
            meta: List[str] = []
            if step.get("duration_ms") is not None:
                meta.append(f"{step['duration_ms']} ms")
            if step.get("tokens") is not None:
                meta.append(f"{step['tokens']} tok")
            if step.get("cost") is not None:
                meta.append(f"${step['cost']:.4f}")
            if meta:
                header += f" ({', '.join(meta)})"
            lines.append(header)
            summary = step.get("summary") or ""
            if len(summary) <= 200:
                lines.append("```")
                lines.append(summary.strip())
                lines.append("```")
            else:
                lines.append(
                    "<details><summary>Summary</summary>\n\n" + summary + "\n\n</details>"
                )
            lines.append("")
    return "\n".join(lines).encode("utf-8")


def write_trace_json(run_id: str, trace: Sequence[Dict[str, Any]]) -> None:
    write_bytes(run_id, "trace", "json", to_json(trace))


def write_trace_csv(run_id: str, trace: Sequence[Dict[str, Any]]) -> None:
    write_bytes(run_id, "summary", "csv", to_csv(trace, run_id=run_id))


def write_trace_markdown(run_id: str, trace: Sequence[Dict[str, Any]]) -> None:
    write_bytes(run_id, "trace", "md", to_markdown(trace, run_id=run_id))


__all__ = [
    "to_json",
    "to_csv",
    "to_markdown",
    "write_trace_json",
    "write_trace_csv",
    "write_trace_markdown",
]
