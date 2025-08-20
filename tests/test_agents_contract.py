import json

from core.agents.research_scientist_agent import ResearchScientistAgent
from core.agents import base_agent


def _res(text):
    return type("R", (), {"content": text})()


def test_agent_output_contract(monkeypatch):
    agent = ResearchScientistAgent("gpt-5")
    sample = (
        '{"role": "Research Scientist", "task": "t", '
        '"findings": ["f"], "risks": ["r"], "next_steps": ["n"], "sources": []}'
    )
    monkeypatch.setattr(base_agent, "complete", lambda s, u, **k: _res(sample))
    result = json.loads(agent.act("idea", "t"))
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
