from core.router import choose_agent_for_task


def test_keyword_routing():
    role, cls = choose_agent_for_task(
        "Finance Analyst", "Budget Planning", "ROI and BOM"
    )
    assert role == "Finance"


def test_default_role():
    role, cls = choose_agent_for_task(
        "Unknown", "Investigate", "quantum entanglement"
    )
    assert role == "Research Scientist"
