from core.agents.unified_registry import AGENT_REGISTRY
from core.router import KEYWORDS, ALIASES, choose_agent_for_task

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

def test_router_resolves_all_registry_roles():
    # Ensure router returns the correct agent class when role is specified
    for role, cls in AGENT_REGISTRY.items():
        resolved, got_cls, _model = choose_agent_for_task(role, "", "")
        assert resolved == role
        assert got_cls is cls


def test_no_unmapped_roles():
    # Ensure every role has a keyword or alias mapping unless explicitly excluded
    mapped = set(KEYWORDS.values()) | set(ALIASES.values())
    unmapped = set(AGENT_REGISTRY) - mapped - EXPLICIT_ROLES
    assert not unmapped, f"unmapped roles: {sorted(unmapped)}"
