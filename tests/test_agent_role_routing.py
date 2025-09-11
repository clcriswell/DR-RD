import pytest

from core.agents.unified_registry import AGENT_REGISTRY
from core.router import KEYWORDS, ALIASES, route_task

# Roles that are invoked explicitly and do not require keyword mapping
EXPLICIT_ROLES = {
    "Planner",
    "Synthesizer",
    "Reflection",
    "Evaluation",
    "Dynamic Specialist",
    "Chief Scientist",
    "Regulatory Specialist",
}


@pytest.mark.parametrize("role", list(AGENT_REGISTRY))
def test_each_role_reachable(role):
    cls = AGENT_REGISTRY[role]
    if role in EXPLICIT_ROLES:
        task = {"title": "t", "description": "d", "role": role}
    else:
        keyword = next((k for k, v in KEYWORDS.items() if v == role), None)
        if keyword:
            task = {"title": "t", "description": keyword}
        else:
            alias = next((k for k, v in ALIASES.items() if v == role), None)
            assert alias, f"no trigger for {role}"
            task = {"title": "t", "description": "", "role": alias}
    routed_role, routed_cls, _model, _ = route_task(task)
    assert routed_role == role
    assert routed_cls is cls


def test_no_unmapped_roles():
    mapped = set(KEYWORDS.values()) | set(ALIASES.values())
    unmapped = set(AGENT_REGISTRY) - mapped - EXPLICIT_ROLES
    assert not unmapped, f"unmapped roles: {sorted(unmapped)}"
