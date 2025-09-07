from core.agents.reflection_agent import ReflectionAgent, PromptFactoryAgent


def test_reflection_agent_proposes_followup(monkeypatch):
    agent = ReflectionAgent("gpt-4o-mini")
    def fake_run_with_spec(self, spec, **_):
        return '["[Finance]: Recheck numbers"]'
    monkeypatch.setattr(PromptFactoryAgent, 'run_with_spec', fake_run_with_spec)
    out = agent.run("idea", {"summary": "", "findings": "Not determined"})
    assert "Finance" in out
