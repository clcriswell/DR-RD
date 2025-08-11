from core.agents.scientist_agent import ResearchScientistAgent


def test_agent_output_contract(monkeypatch):
    agent = ResearchScientistAgent(model_id="gpt-3.5-turbo")
    sample = (
        '{"role": "Research", "task": "t", '
        '"findings": ["f"], "risks": ["r"], "next_steps": ["n"]}'
    )
    monkeypatch.setattr(agent, "_call_openai", lambda task, context: sample)
    result = agent.act("t")
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
