from __future__ import annotations

"""Simple reporting pipeline helpers.

This module provides :func:`build_report` which assembles a markdown and HTML
representation of an audit report. The implementation is intentionally
lightweight – tests ensure sections render, references map to stable identifiers
and secret values are redacted.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

import yaml

try:  # optional markdown conversion
    import markdown  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    markdown = None

from utils.redaction import load_policy, redact_text

# ---------------------------------------------------------------------------
# Redaction helpers

_DEF_POLICY_PATH = Path("config/redaction.yaml")


def _redact(text: str) -> str:
    """Redact ``text`` using the central policy."""
    if not text:
        return text
    try:
        policy = load_policy(_DEF_POLICY_PATH)
    except Exception:  # pragma: no cover - config optional
        policy = {}
    return redact_text(text, policy=policy)


@dataclass
class ReportOptions:
    include_sections: Optional[Iterable[str]] = None
    title: str = "Report"
    author: str = ""


_DEFAULT_SECTIONS = [
    "title",
    "executive_summary",
    "plan",
    "findings",
    "risks",
    "simulations",
    "compliance",
    "references",
    "appendix",
]


# ---------------------------------------------------------------------------
# Core builder


def _section_enabled(name: str, opts: ReportOptions) -> bool:
    if not opts.include_sections:
        return True
    return name in set(opts.include_sections)


def _render_references(sources: Iterable[Mapping[str, str]]) -> str:
    lines = ["## References"]
    for idx, src in enumerate(sources, start=1):
        url = _redact(str(src.get("url", "")))
        title = _redact(str(src.get("title", url)))
        lines.append(f"[S{idx}] {title} - {url}")
    return "\n".join(lines)


def build_report(
    state: Mapping[str, object] | None,
    answers: Mapping[str, object] | None,
    sources: Iterable[Mapping[str, str]] | None,
    options: Mapping[str, object] | None = None,
) -> Dict[str, object]:
    """Build a report in markdown and HTML."""

    opts = ReportOptions(**(options or {}))
    md_lines: List[str] = []

    # Title -----------------------------------------------------------------
    if _section_enabled("title", opts):
        md_lines.append(f"# {_redact(opts.title)}")
        if opts.author:
            md_lines.append(f"_Author: {_redact(opts.author)}_")
        md_lines.append("")

    # Executive summary -----------------------------------------------------
    if _section_enabled("executive_summary", opts):
        summary = _redact(str((state or {}).get("summary", "")))
        md_lines.append("## Executive Summary")
        md_lines.append(summary or "(none)")
        md_lines.append("")

    # Plan & Tasks ----------------------------------------------------------
    if _section_enabled("plan", opts):
        plan = _redact(str((state or {}).get("plan", "")))
        md_lines.append("## Plan & Tasks")
        md_lines.append(plan or "(none)")
        md_lines.append("")

    # Key Findings ----------------------------------------------------------
    if _section_enabled("findings", opts):
        md_lines.append("## Key Findings")
        if answers:
            for role, text in answers.items():
                md_lines.append(f"### { _redact(str(role)) }")
                md_lines.append(_redact(str(text)))
                md_lines.append("")
        else:
            md_lines.append("(none)\n")

    # Risks & Next Steps ----------------------------------------------------
    if _section_enabled("risks", opts):
        risks = _redact(str((state or {}).get("risks", "")))
        md_lines.append("## Risks & Next Steps")
        md_lines.append(risks or "(none)")
        md_lines.append("")

    # Simulations -----------------------------------------------------------
    if _section_enabled("simulations", opts):
        sims = _redact(str((state or {}).get("simulations", "")))
        md_lines.append("## Simulations")
        md_lines.append(sims or "(none)")
        md_lines.append("")

    # Compliance ------------------------------------------------------------
    if _section_enabled("compliance", opts):
        comp = _redact(str((state or {}).get("compliance", "")))
        md_lines.append("## Compliance")
        md_lines.append(comp or "(none)")
        md_lines.append("")

    # References ------------------------------------------------------------
    if _section_enabled("references", opts) and sources:
        md_lines.append(_render_references(sources))
        md_lines.append("")

    # Appendix --------------------------------------------------------------
    if _section_enabled("appendix", opts):
        meta = yaml.safe_dump((state or {}).get("meta", {}))
        md_lines.append("## Appendix")
        md_lines.append(f"```\n{_redact(meta)}\n```")

    markdown_text = "\n".join(md_lines).strip() + "\n"
    html_text = (
        markdown.markdown(markdown_text) if markdown else f"<pre>{markdown_text}</pre>"
    )

    return {
        "markdown": markdown_text,
        "html": html_text,
        "meta": {"sections": opts.include_sections or _DEFAULT_SECTIONS},
    }
