from core.router import choose_agent_for_task
from core.agents.unified_registry import AGENT_REGISTRY


def test_keyword_routing():
    role, cls, _ = choose_agent_for_task(
        None, "Budget Planning", "ROI and BOM", None
    )
    assert role == "Finance"
    assert cls is AGENT_REGISTRY["Finance"]


def test_default_role():
    role, cls, _ = choose_agent_for_task(
        None, "Investigate", "quantum entanglement", None
    )
    assert role == "Research Scientist"
    assert cls is AGENT_REGISTRY["Research Scientist"]
