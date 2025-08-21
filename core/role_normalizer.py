from __future__ import annotations

from difflib import get_close_matches
from collections import Counter
from typing import Dict, List, Set

# Map canonical role names to sets of specialist synonyms
SYNONYMS: Dict[str, Set[str]] = {
    "Mechanical Systems Lead": {
        "Mechanical Engineer",
        "Manufacturing Engineer",
        "Tooling Engineer",
        "Prototyping Technician",
        "Automation Engineer",
        "Controls Engineer",
        "Operations Manager",
        "Packaging Engineer",
    },
    "Regulatory": {
        "Quality Engineer",
        "Regulatory/Compliance Specialist",
        "Environmental Specialist",
        "Test Engineer",
        "QA Manager",
    },
    "Planner": {
        "Product Manager",
        "Program Manager",
        "Project Manager",
        "Logistics Manager",
    },
    "Finance": {
        "Cost Analyst",
        "Supply Chain Manager",
        "Procurement",
        "Sourcing Manager",
    },
    "Marketing Analyst": {
        "Sales Manager",
        "Channel Manager",
        "Brand Manager",
        "Product Marketing",
    },
    "Research Scientist": {
        "Materials Engineer",
        "Materials Scientist",
        "Coating Process Engineer",
        "R&D Scientist",
    },
    "IP Analyst": {
        "Patent Analyst",
        "IP Counsel",
        "Patent Engineer",
    },
    "CTO": {
        "Chief Engineer",
        "Technical Lead",
        "Systems Architect",
    },
    "Synthesizer": set(),
}

# Precompute reverse lookup for synonyms (case-insensitive)
_LOOKUP: Dict[str, str] = {}
for canon, syns in SYNONYMS.items():
    _LOOKUP[canon.lower()] = canon
    for s in syns:
        _LOOKUP[s.lower()] = canon


def normalize_role(name: str, allowed_roles: Set[str]) -> str:
    """Map a specialist role name to a canonical allowed role.

    Parameters
    ----------
    name: The role name suggested by the planner.
    allowed_roles: Set of canonical role names permitted by the system.
    """

    if not name:
        return "Synthesizer"

    allowed_map = {r.lower(): r for r in allowed_roles}
    raw = name.strip()
    low = raw.lower()

    if low in allowed_map:
        return allowed_map[low]

    hit = _LOOKUP.get(low)
    if hit and hit in allowed_roles:
        return hit

    match = get_close_matches(raw, list(allowed_roles), n=1, cutoff=0.75)
    if match:
        return match[0]

    return "Synthesizer"


def normalize_tasks(
    tasks: List[Dict],
    *,
    allowed_roles: Set[str],
    max_roles: int | None = None,
) -> List[Dict]:
    """Attach ``normalized_role`` to each task and optionally limit distinct roles."""

    normalized: List[Dict] = []
    for t in tasks:
        role = str(t.get("role", ""))
        norm = normalize_role(role, allowed_roles)
        normalized.append({**t, "normalized_role": norm})

    if max_roles is not None and max_roles > 0:
        freq = Counter(t["normalized_role"] for t in normalized)
        if len(freq) > max_roles:
            keep = {r for r, _ in freq.most_common(max_roles)}
            for t in normalized:
                if t["normalized_role"] not in keep:
                    t["normalized_role"] = "Synthesizer"

    return normalized


def group_by_role(tasks: List[Dict], *, key: str) -> Dict[str, List[Dict]]:
    """Group tasks by ``key`` value."""

    grouped: Dict[str, List[Dict]] = {}
    for t in tasks:
        role = t.get(key, "Synthesizer")
        grouped.setdefault(role, []).append(t)
    return grouped

