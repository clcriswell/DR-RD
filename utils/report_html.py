from __future__ import annotations

"""HTML report builder for DR RD runs."""

from datetime import datetime
import html
from typing import Callable, Mapping, Sequence, Tuple

from .report_builder import summarize_steps


def _esc(text: object | None) -> str:
    """HTML-escape ``text`` converted to string."""
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def _iso(ts: object | None) -> str:
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(ts).isoformat()
        except Exception:
            return ""
    return ""


def _short(text: str | None, limit: int = 80) -> str:
    text = text or ""
    return text[:limit]


CSS = (
    "body{font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,\"Helvetica Neue\",Arial,sans-serif;"
    "font-size:16px;line-height:1.5;color:#0A0A0A;background:#FFFFFF;padding:1rem;}"
    "h1,h2,h3{color:#0A0A0A;}"
    "table{width:100%;border-collapse:collapse;margin-top:1rem;}"
    "th,td{border:1px solid #ddd;padding:4px 8px;text-align:left;}"
    "th{background:#F6F8FA;}"
    ".chip{display:inline-block;padding:0 8px;border-radius:9999px;font-size:12px;line-height:20px;}"
    ".chip.complete{background:#ECFDF5;color:#065F46;}"
    ".chip.error{background:#FEE2E2;color:#991B1B;}"
    ".chip.running{background:#FEF3C7;color:#92400E;}"
    ".metrics{display:flex;flex-wrap:wrap;gap:0.5rem;margin:1rem 0;}"
    ".metric{background:#F6F8FA;padding:8px 12px;border-radius:4px;}"
    ".metric .label{font-size:0.875rem;color:#555;}"
    ".metric .value{font-weight:600;}"
    "@media print{a[href]:after{content:''}.no-print{display:none}table{page-break-inside:auto}tr{page-break-inside:avoid}}"
)


def build_html_report(
    run_id: str,
    meta: Mapping,
    rows: Sequence[Mapping],
    summary_text: str | None,
    totals: Mapping | None,
    artifacts: Sequence[Tuple[str, str]] | None = None,
    sanitizer: Callable[[str], str] | None = None,
) -> str:
    """Return a complete UTF-8 HTML report string."""

    lines: list[str] = []
    lines.append("<!DOCTYPE html>")
    lines.append("<html lang=\"en\">")
    lines.append("<head>")
    lines.append("<meta charset=\"utf-8\">")
    lines.append(f"<title>DR RD Report — {_esc(run_id)}</title>")
    lines.append("<style>" + CSS + "</style>")
    lines.append("</head>")
    lines.append("<body>")
    lines.append(f"<h1>DR RD Report — {_esc(run_id)}</h1>")

    # Overview
    lines.append("<h2>Overview</h2>")
    idea = meta.get("idea_preview")
    if sanitizer and isinstance(idea, str):
        idea = sanitizer(idea)
    mode = meta.get("mode")
    started = _iso(meta.get("started_at"))
    completed = _iso(meta.get("completed_at"))
    duration = ""
    if meta.get("started_at") and meta.get("completed_at"):
        try:
            duration = str(int(meta["completed_at"] - meta["started_at"])) + " s"
        except Exception:
            duration = ""
    if idea:
        lines.append(f"<p><strong>Idea:</strong> {_esc(idea)}</p>")
    if mode:
        lines.append(f"<p><strong>Mode:</strong> {_esc(mode)}</p>")
    if started:
        lines.append(f"<p><strong>Started:</strong> {_esc(started)}</p>")
    if completed:
        lines.append(f"<p><strong>Completed:</strong> {_esc(completed)}</p>")
    if duration:
        lines.append(f"<p><strong>Duration:</strong> {_esc(duration)}</p>")

    # Key results
    lines.append("<h2>Key results</h2>")
    if summary_text:
        txt = sanitizer(summary_text) if sanitizer else summary_text
        lines.append("<pre><code>")
        lines.append(_esc(txt))
        lines.append("</code></pre>")
    else:
        summaries = summarize_steps(rows)
        if summaries:
            lines.append("<ul>")
            for s in summaries:
                txt = sanitizer(s) if sanitizer else s
                lines.append(f"<li>{_esc(txt)}</li>")
            lines.append("</ul>")

    # Metrics
    lines.append("<h2>Metrics</h2>")
    lines.append("<div class=\"metrics\">")
    lines.append(
        f"<div class=\"metric\"><span class=\"label\">Steps</span><span class=\"value\">{len(rows)}</span></div>"
    )
    if totals:
        tokens = totals.get("tokens") if isinstance(totals, Mapping) else None
        cost = totals.get("cost") if isinstance(totals, Mapping) else None
        if tokens is not None:
            lines.append(
                f"<div class=\"metric\"><span class=\"label\">Tokens</span><span class=\"value\">{_esc(tokens)}</span></div>"
            )
        if cost is not None:
            lines.append(
                f"<div class=\"metric\"><span class=\"label\">Cost</span><span class=\"value\">${float(cost):.4f}</span></div>"
            )
    lines.append("</div>")

    # Trace table
    lines.append("<h2>Trace</h2>")
    lines.append(
        "<table><thead><tr><th>#</th><th>Phase</th><th>Name</th><th>Status</th><th>Duration (ms)</th><th>Tokens</th><th>Cost</th><th>Summary</th></tr></thead><tbody>"
    )
    for r in rows:
        status = r.get("status")
        chip = f"<span class=\"chip {status}\">{_esc(status)}</span>" if status else ""
        lines.append(
            "<tr>"
            f"<td>{_esc(r.get('i'))}</td>"
            f"<td>{_esc(r.get('phase'))}</td>"
            f"<td>{_esc(r.get('name'))}</td>"
            f"<td>{chip}</td>"
            f"<td>{_esc(r.get('duration_ms'))}</td>"
            f"<td>{_esc(r.get('tokens'))}</td>"
            f"<td>{_esc(r.get('cost'))}</td>"
            f"<td>{_esc(_short(r.get('summary')))}</td>"
            "</tr>"
        )
    lines.append("</tbody></table>")

    # Errors
    errors = [r for r in rows if r.get("status") == "error"]
    if errors:
        lines.append("<h2>Errors</h2>")
        lines.append("<ul>")
        for e in errors:
            lines.append(
                f"<li>{_esc(e.get('name'))} — {_esc(e.get('summary'))}</li>"
            )
        lines.append("</ul>")

    # Artifacts
    if artifacts:
        lines.append("<h2>Artifacts</h2>")
        lines.append("<ul>")
        for name, rel in artifacts:
            href = _esc(rel)
            lines.append(f"<li><a href=\"{href}\">{_esc(name)}</a></li>")
        lines.append("</ul>")

    lines.append("</body></html>")
    return "\n".join(lines)


__all__ = ["build_html_report"]
