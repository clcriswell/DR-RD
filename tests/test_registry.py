from core.router import choose_agent_for_task
from core.agents.unified_registry import AGENT_REGISTRY


def test_agent_mapping_cto():
    role, cls, _ = choose_agent_for_task(
        None, "Evaluate system architecture and risk", ""
    )
    assert role == "CTO" and cls is AGENT_REGISTRY["CTO"]


def test_agent_mapping_research():
    role, cls, _ = choose_agent_for_task(
        None, "Survey materials and physics literature", ""
    )
    assert role == "Research Scientist" and cls is AGENT_REGISTRY["Research Scientist"]


def test_agent_mapping_regulatory():
    role, cls, _ = choose_agent_for_task(
        None, "Check FDA compliance and ISO standards", ""
    )
    assert role == "Regulatory" and cls is AGENT_REGISTRY["Regulatory"]


def test_agent_mapping_finance_keyword():
    role, cls, _ = choose_agent_for_task(
        None, "Estimate BOM cost and budget", ""
    )
    assert role == "Finance" and cls is AGENT_REGISTRY["Finance"]


def test_agent_exact_role_over_keyword():
    role, cls, _ = choose_agent_for_task(
        "Finance", "Analyze competitor pricing and market segments", ""
    )
    assert role == "Finance" and cls is AGENT_REGISTRY["Finance"]


def test_agent_mapping_default():
    role, cls, _ = choose_agent_for_task(None, "Unrecognized task", "")
    assert role == "Research Scientist" and cls is AGENT_REGISTRY["Research Scientist"]
