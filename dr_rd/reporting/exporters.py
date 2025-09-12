from __future__ import annotations

import html
from typing import Dict, List, Optional


def to_markdown(report: Dict) -> str:
    lines: List[str] = [f"# {report['title']}", "", report.get("executive_summary", ""), ""]
    sections = report.get("sections", [])
    grouped_mode = any(s.get("group") for s in sections)
    current_group: Optional[str] = None
    for sec in sections:
        group = sec.get("group")
        if grouped_mode and group:
            if group != current_group:
                lines.append(f"## {group}")
                lines.append("")
                current_group = group
            lines.append(f"### {sec['heading']}")
        else:
            lines.append(f"## {sec['heading']}")
        lines.append(sec.get("body_md", ""))
        lines.append("")
    planner = report.get("metadata", {}).get("planner", {})
    constraints = planner.get("constraints") or []
    assumptions = planner.get("assumptions") or []
    if constraints or assumptions:
        lines.append("## Constraints / Assumptions")
        for c in constraints:
            lines.append(f"- {c}")
        for a in assumptions:
            lines.append(f"- {a}")
        lines.append("")
    risks = planner.get("risks") or []
    if risks:
        lines.append("## Risks")
        for r in risks:
            lines.append(f"- {r}")
        lines.append("")
    if report.get("sources"):
        lines.append("## Sources")
        for i, s in enumerate(report["sources"], 1):
            title = s.get("title") or s.get("url", "")
            url = s.get("url") or ""
            lines.append(f"[{i}] {title} {url}".strip())
    return "\n".join(lines).strip() + "\n"


HTML_TEMPLATE = (
    "<html><head><meta charset='utf-8'><style>"
    "body{{font-family:Arial,sans-serif;margin:40px;}}"
    "h1{{font-size:24px;}}h2{{font-size:20px;}}pre{{white-space:pre-wrap;}}"
    "</style></head><body>{content}</body></html>"
)


def to_html(report: Dict) -> str:
    md = to_markdown(report)
    esc = html.escape(md).replace("\n", "<br/>")
    return HTML_TEMPLATE.format(content=esc)
