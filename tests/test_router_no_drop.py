from core.router import choose_agent_for_task
from core.agents.registry import AGENT_REGISTRY


def test_keyword_routing():
    role, cls = choose_agent_for_task(
        None, "Budget Planning", "ROI and BOM"
    )
    assert role == "Finance"
    assert cls is AGENT_REGISTRY["Finance"]


def test_default_role():
    role, cls = choose_agent_for_task(
        None, "Investigate", "quantum entanglement"
    )
    assert role == "Research Scientist"
    assert cls is AGENT_REGISTRY["Research Scientist"]
