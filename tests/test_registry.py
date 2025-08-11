from core.agents import registry


def test_agent_mapping_cto():
    agents = registry.build_agents("test")
    agent = registry.get_agent_for_task("Evaluate system architecture and risk", agents)
    assert agent.name == "CTO"


def test_agent_mapping_research():
    agents = registry.build_agents("test")
    agent = registry.get_agent_for_task("Survey materials and physics literature", agents)
    assert agent.name == "Research"


def test_agent_mapping_regulatory():
    agents = registry.build_agents("test")
    agent = registry.get_agent_for_task("Check FDA compliance and ISO standards", agents)
    assert agent.name == "Regulatory"


def test_agent_mapping_finance():
    agents = registry.build_agents("test")
    agent = registry.get_agent_for_task("Estimate BOM cost and budget", agents)
    assert agent.name == "Finance"


def test_agent_mapping_default():
    agents = registry.build_agents("test")
    agent = registry.get_agent_for_task("Unrecognized task", agents)
    assert agent.name == "Research"
