from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List

from .citations import bundle_citations, merge_agent_sources, normalize_sources
from dr_rd.kb.models import KBSource


def compose(spec: Dict, artifacts: Dict) -> Dict:
    """Build a report object from agent artifacts and a plan spec."""
    agents = artifacts.get("agents", [])
    synth = artifacts.get("synth", {})
    sections_data: List[tuple[str, List[KBSource]]] = []
    all_sources: List[KBSource] = []
    for a in agents:
        body = a.get("body", "")
        sources = normalize_sources(a.get("sources", []))
        sections_data.append((body, sources))
        all_sources.extend(sources)
    processed_sections, bundled_sources = bundle_citations(sections_data)
    sections = []
    for a, body in zip(agents, processed_sections):
        sections.append({"heading": a.get("title", a.get("role", "")), "body_md": body})
    report = {
        "report_id": spec.get("report_id", "r1"),
        "title": spec.get("title", "Report"),
        "executive_summary": synth.get("executive_summary", ""),
        "sections": sections,
        "sources": [s.__dict__ for s in bundled_sources],
        "metadata": {
            "planner": spec.get("planner", {}),
            "roles_used": [a.get("role") for a in agents],
            "flags": spec.get("flags", {}),
        },
        "generated_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return report
