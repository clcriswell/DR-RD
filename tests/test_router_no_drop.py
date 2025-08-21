from core.router import choose_agent_for_task
from core.agents.registry import AGENT_REGISTRY


def test_keyword_routing():
    role, cls, _ = choose_agent_for_task(
        None, "Budget Planning", "ROI and BOM"
    )
    assert role == "Finance"
    assert cls is AGENT_REGISTRY["Finance"]


def test_default_role():
    role, cls, _ = choose_agent_for_task(
        None, "Investigate", "quantum entanglement"
    )
    assert role == "Synthesizer"
    assert cls is AGENT_REGISTRY["Synthesizer"]
