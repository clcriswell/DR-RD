from core.agents import registry


def test_agent_mapping_cto():
    agents = registry.build_agents("test")
    agent, role = registry.choose_agent_for_task(
        None, "Evaluate system architecture and risk", agents
    )
    assert agent.name == "CTO" and role == "CTO"


def test_agent_mapping_research():
    agents = registry.build_agents("test")
    agent, role = registry.choose_agent_for_task(
        None, "Survey materials and physics literature", agents
    )
    assert agent.name == "Research" and role == "Research"


def test_agent_mapping_regulatory():
    agents = registry.build_agents("test")
    agent, role = registry.choose_agent_for_task(
        None, "Check FDA compliance and ISO standards", agents
    )
    assert agent.name == "Regulatory" and role == "Regulatory"


def test_agent_mapping_finance_keyword():
    agents = registry.build_agents("test")
    agent, role = registry.choose_agent_for_task(
        None, "Estimate BOM cost and budget", agents
    )
    assert agent.name == "Finance" and role == "Finance"


def test_agent_exact_role_over_keyword():
    agents = registry.build_agents("test")
    agent, role = registry.choose_agent_for_task(
        "Finance", "Analyze competitor pricing and market segments", agents
    )
    assert agent.name == "Finance" and role == "Finance"


def test_agent_mapping_default():
    agents = registry.build_agents("test")
    agent, role = registry.choose_agent_for_task(None, "Unrecognized task", agents)
    assert agent.name == "Research" and role == "Research"
