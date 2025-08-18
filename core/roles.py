from typing import Optional, Set

CANONICAL = {
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

def normalize_role(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    return CANONICAL.get(name.strip().lower())

def canonical_roles() -> Set[str]:
    return {"CTO","Research Scientist","Regulatory","Finance","Marketing Analyst","IP Analyst"}
