from __future__ import annotations

import time
from typing import Any

from dr_rd.kb.models import KBSource

from .citations import bundle_citations, normalize_sources


def compose(spec: dict[str, Any], artifacts: dict[str, Any]) -> dict[str, Any]:
    """Build a report object from agent artifacts and a plan spec."""
    agents = artifacts.get("agents", [])
    synth = artifacts.get("synth", {})
    sections_data: list[tuple[str, list[KBSource]]] = []
    for a in agents:
        body = a.get("body", "")
        sources = normalize_sources(a.get("sources", []))
        sections_data.append((body, sources))
    processed_sections, bundled_sources = bundle_citations(sections_data)
    sections = []
    for a, body in zip(agents, processed_sections):
        sections.append(
            {
                "heading": a.get("title", a.get("role", "")),
                "body_md": body,
                "group": a.get("group"),
            }
        )
    planner_meta = spec.get("planner", {}).copy()
    risk_reg = planner_meta.get("risk_register")
    if isinstance(risk_reg, list):
        planner_meta.setdefault("risks", [])
        planner_meta["risks"].extend(
            [r.get("class", str(r)) if isinstance(r, dict) else str(r) for r in risk_reg]
        )
    contradictions = synth.get("contradictions")
    if not isinstance(contradictions, list):
        contradictions = []

    report = {
        "report_id": spec.get("report_id", "r1"),
        "title": spec.get("title", "Report"),
        "executive_summary": synth.get("executive_summary", ""),
        "sections": sections,
        "sources": [s.__dict__ for s in bundled_sources],
        "metadata": {
            "planner": planner_meta,
            "roles_used": [a.get("role") for a in agents],
            "flags": spec.get("flags", {}),
        },
        "generated_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    report["contradictions"] = contradictions

    confidence = synth.get("confidence")
    if isinstance(confidence, (int, float)):
        report["confidence"] = float(confidence)

    return report
