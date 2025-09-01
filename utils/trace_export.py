from __future__ import annotations

import csv
import io
import json
from collections import OrderedDict
from typing import Any, Callable, Mapping, Sequence

from .paths import write_bytes

Row = list[Any]
TraceStep = Mapping[str, Any]
TraceRow = dict[str, Any]


def _safe_summary(text: str | None, max_len: int = 80) -> str:
    """Return ``text`` truncated to ``max_len`` characters.

    ``trace`` rows may contain summary fields that are not simple strings.
    Previously we attempted to slice these values directly which raised a
    ``KeyError`` when the summary was a ``dict`` or other mapping type.  To
    make the export utilities robust we coerce any non-string input to a
    string before truncation.
    """

    if text is None:
        text = ""
    elif not isinstance(text, str):
        text = str(text)
    return text[:max_len]


def flatten_trace_rows(trace: Sequence[TraceStep]) -> list[dict]:
    """Return normalized rows for tabular exports.

    Each row contains the fields: i, id, parents, phase, name, status,
    duration_ms, tokens, cost, summary, prompt, citations.
    """
    rows: list[dict] = []
    for idx, step in enumerate(trace, 1):
        summary = step.get("summary")
        if not summary:
            summary = step.get("output") or step.get("result") or step.get("text") or ""
        prompt = step.get("prompt") or step.get("prompt_preview")

        tokens = step.get("tokens")
        if tokens is None:
            tokens = (step.get("tokens_in") or 0) + (step.get("tokens_out") or 0)

        cost = step.get("cost")
        if cost is None:
            cost = step.get("cost_usd")

        rows.append(
            {
                "i": idx,
                "id": step.get("id"),
                "parents": step.get("parent_ids") or step.get("parents"),
                "phase": step.get("phase"),
                "name": step.get("name"),
                "status": step.get("status"),
                "duration_ms": step.get("duration_ms"),
                "tokens": tokens,
                "cost": cost,
                "summary": summary,
                "prompt": prompt,
                "citations": step.get("citations"),
            }
        )
    return rows


def to_json(trace: Sequence[dict[str, Any]]) -> bytes:
    """Return the trace as JSON bytes."""
    return json.dumps(list(trace), ensure_ascii=False, indent=2).encode("utf-8")


def to_csv(
    trace: Sequence[dict[str, Any]],
    run_id: str | None = None,
    sanitizer: Callable[[str], str] | None = None,
) -> bytes:
    """Return a CSV summary of the trace."""
    rows = flatten_trace_rows(trace)
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(
        [
            "run_id",
            "phase",
            "step_index",
            "name",
            "status",
            "duration_ms",
            "tokens",
            "cost",
            "summary_80chars",
            "citations_json",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                run_id,
                row.get("phase"),
                row.get("i"),
                row.get("name"),
                row.get("status"),
                row.get("duration_ms"),
                row.get("tokens"),
                row.get("cost"),
                _safe_summary(sanitizer(row.get("summary")) if sanitizer else row.get("summary")),
                json.dumps(row.get("citations", []), ensure_ascii=False),
            ]
        )
    return output.getvalue().encode("utf-8")


def to_markdown(
    trace: Sequence[dict[str, Any]],
    run_id: str | None = None,
    sanitizer: Callable[[str], str] | None = None,
) -> bytes:
    """Return a human readable Markdown report of the trace."""
    phases: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for step in trace:
        phase = (step.get("phase") or "unknown").lower()
        phases.setdefault(phase, []).append(step)

    lines: list[str] = []
    title = f"Trace {run_id}" if run_id else "Trace"
    lines.append(f"# {title}\n")
    for phase, steps in phases.items():
        lines.append(f"## {phase.capitalize()}\n")
        total = len(steps)
        for i, step in enumerate(steps, 1):
            status = step.get("status")
            badge = {"complete": "✅", "error": "⚠️", "running": "⏳"}.get(status, "")
            header = f"### Step {i}/{total} — {step.get('name', '')} {badge}".rstrip()
            meta: list[str] = []
            if step.get("duration_ms") is not None:
                meta.append(f"{step['duration_ms']} ms")
            if step.get("tokens") is not None:
                meta.append(f"{step['tokens']} tok")
            if step.get("cost") is not None:
                meta.append(f"${step['cost']:.4f}")
            if meta:
                header += f" ({', '.join(meta)})"
            lines.append(header)
            raw_summary = step.get("summary")
            if not raw_summary:
                raw_summary = step.get("output") or step.get("result") or step.get("text") or ""
            summary = _safe_summary(raw_summary, max_len=10_000)
            if sanitizer:
                summary = sanitizer(summary)
            if len(summary) <= 200:
                lines.append("```")
                lines.append(summary.strip())
                lines.append("```")
            else:
                lines.append("<details><summary>Summary</summary>\n\n" + summary + "\n\n</details>")
            lines.append("")
    return "\n".join(lines).encode("utf-8")


def write_trace_json(run_id: str, trace: Sequence[dict[str, Any]]) -> None:
    write_bytes(run_id, "trace", "json", to_json(trace))


def write_trace_csv(
    run_id: str, trace: Sequence[dict[str, Any]], sanitizer: Callable[[str], str] | None = None
) -> None:
    write_bytes(run_id, "summary", "csv", to_csv(trace, run_id=run_id, sanitizer=sanitizer))


def write_trace_markdown(
    run_id: str, trace: Sequence[dict[str, Any]], sanitizer: Callable[[str], str] | None = None
) -> None:
    write_bytes(run_id, "trace", "md", to_markdown(trace, run_id=run_id, sanitizer=sanitizer))


__all__ = [
    "to_json",
    "to_csv",
    "to_markdown",
    "write_trace_json",
    "write_trace_csv",
    "write_trace_markdown",
    "flatten_trace_rows",
]
