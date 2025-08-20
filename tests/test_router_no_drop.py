from orchestrators.router import choose_agent_for_task


class Dummy:
    pass


def test_unknown_role_does_not_drop(monkeypatch):
    agents = {"Research Scientist": Dummy(), "Finance": Dummy(), "Regulatory": Dummy()}
    # planned role not in agents, but finance keywords route it
    agent, role = choose_agent_for_task(
        "Finance Analyst", "Budget Planning", "ROI and BOM", ["finance"], agents
    )
    assert role in agents


def test_alias_maps_to_known():
    agents = {"Research Scientist": Dummy()}
    agent, role = choose_agent_for_task(
        "Research", "Investigate", "quantum entanglement", [], agents
    )
    assert role == "Research Scientist"
