import logging
import os
from typing import Set

# Strict mode may reject unmapped roles.  Setting HRM_STRICT_ROLE_NORMALIZATION=false
# is recommended unless strict behavior is explicitly desired.
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
    "hrm": "HRM",
    "human resources": "HRM",
    "materials engineer": "Materials Engineer",
    "reflection": "Reflection",
    "dynamic specialist": "Dynamic Specialist",
    "qa": "QA",
    "quality assurance": "QA",
}

# Additional explicit role remappings to stop Synthesizer fallbacks. The keys
# are human-facing roles that may appear in planner output; the values are the
# canonical registry roles.  Each mapping is annotated with a comment explaining
# the rationale for the merge.
CANONICAL = {
    # Mechanical work is handled by the Mechanical Systems Lead agent.
    "Mechanical Engineer": "Mechanical Systems Lead",
    # Electrical considerations map best to the CTO for high-level architecture.
    "Electrical Engineer": "CTO",
    # Software engineering tasks are covered by the Research Scientist agent.
    "Software Engineer": "Research Scientist",
    # UX/UI planning feeds into market analysis for the product.
    "UX/UI Designer": "Marketing Analyst",
    # Materials research is handled by the Mechanical Systems Lead today.
    "Materials Scientist": "Mechanical Systems Lead",
    # HR related planning maps to HRM agent
    "Human Resources": "HRM",
}

logger = logging.getLogger(__name__)


def normalize_role(role: str | None) -> str | None:
    if not role:
        return None
    r = " ".join(role.split()).strip()
    low = r.lower()
    hit = CANON.get(low)
    if STRICT:
        return hit or r
    return hit or r


def canonicalize(role: str | None) -> str | None:
    """Map variant roles to canonical agent registry roles."""

    if not role:
        return role
    r = " ".join(role.split()).strip()
    mapped = CANONICAL.get(r) or CANONICAL.get(r.lower(), None)
    if mapped and mapped != r:
        logger.info("RoleMap from='%s' to='%s'", r, mapped)
        return mapped
    return r


def canonical_roles() -> Set[str]:
    return {
        "CTO",
        "Research Scientist",
        "Regulatory",
        "Finance",
        "Marketing Analyst",
        "IP Analyst",
        "HRM",
        "Materials Engineer",
        "Reflection",
        "Dynamic Specialist",
    }
