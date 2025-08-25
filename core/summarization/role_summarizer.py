from __future__ import annotations

from typing import Dict, List

from .schemas import RoleSummary


def summarize_role(agent_json: Dict) -> RoleSummary:
    """Create a ``RoleSummary`` from an agent's raw JSON output."""

    role = agent_json.get("role") or agent_json.get("name") or "Unknown"
    findings = agent_json.get("findings") or []
    bullets: List[str] = []
    for f in findings:
        if isinstance(f, str):
            bullets.append(f.strip())
        elif isinstance(f, dict):
            bullets.append(str(f.get("text") or f.get("bullet") or "").strip())
        if len(bullets) == 5:
            break
    return RoleSummary(role=role, bullets=bullets)
