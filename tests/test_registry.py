from core.router import choose_agent_for_task
from core.agents.unified_registry import AGENT_REGISTRY


def test_agent_mapping_cto():
    role, cls, _ = choose_agent_for_task(
        None, "Evaluate system architecture and risk", "", None
    )
    assert role == "CTO" and cls is AGENT_REGISTRY["CTO"]


def test_agent_mapping_research():
    role, cls, _ = choose_agent_for_task(
        None, "Survey materials and physics literature", "", None
    )
    assert role == "Research Scientist" and cls is AGENT_REGISTRY["Research Scientist"]


def test_agent_mapping_regulatory():
    role, cls, _ = choose_agent_for_task(
        None, "Check FDA compliance and ISO standards", "", None
    )
    assert role == "Regulatory" and cls is AGENT_REGISTRY["Regulatory"]


def test_agent_mapping_finance_keyword():
    role, cls, _ = choose_agent_for_task(
        None, "Estimate BOM cost and budget", "", None
    )
    assert role == "Finance" and cls is AGENT_REGISTRY["Finance"]


def test_agent_exact_role_over_keyword():
    role, cls, _ = choose_agent_for_task(
        "Finance", "Analyze competitor pricing and market segments", "", None
    )
    assert role == "Finance" and cls is AGENT_REGISTRY["Finance"]


def test_agent_mapping_default():
    role, cls, _ = choose_agent_for_task(None, "Unrecognized task", "", None)
    assert role == "Dynamic Specialist" and cls is AGENT_REGISTRY["Dynamic Specialist"]
