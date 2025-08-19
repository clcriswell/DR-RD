import os
from typing import Set

STRICT = os.getenv("HRM_STRICT_ROLE_NORMALIZATION", "false").lower() == "true"

CANON = {
    "cto": "CTO",
    "chief technology officer": "CTO",

    "research scientist": "Research Scientist",
    "research": "Research Scientist",

    "regulatory": "Regulatory",
    "regulatory & compliance lead": "Regulatory",
    "compliance": "Regulatory",
    "legal": "Regulatory",

    "finance": "Finance",

    "marketing analyst": "Marketing Analyst",
    "marketing": "Marketing Analyst",

    "ip analyst": "IP Analyst",
    "intellectual property": "IP Analyst",
    "ip": "IP Analyst",
}


def normalize_role(role: str | None) -> str | None:
    if not role:
        return None
    r = " ".join(role.split()).strip()
    low = r.lower()
    hit = CANON.get(low)
    if STRICT:
        return hit
    return hit or r


def canonical_roles() -> Set[str]:
    return {"CTO", "Research Scientist", "Regulatory", "Finance", "Marketing Analyst", "IP Analyst"}
