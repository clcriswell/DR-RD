from core.agents.research_scientist_agent import ResearchScientistAgent


def test_agent_output_contract(monkeypatch):
    agent = ResearchScientistAgent("gpt-5")
    sample = (
        '{"role": "Research", "task": "t", '
        '"findings": ["f"], "risks": ["r"], "next_steps": ["n"], "sources": []}'
    )
    monkeypatch.setattr(agent, "_call_openai", lambda idea, task, context: sample)
    result = agent.act("idea", "t")
    assert set(result.keys()) >= {
        "role",
        "task",
        "findings",
        "risks",
        "next_steps",
    }
    assert isinstance(result["findings"], list)
    assert isinstance(result["risks"], list)
    assert isinstance(result["next_steps"], list)
