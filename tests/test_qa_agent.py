import json

from core.agents.qa_agent import QAAgent
from core.llm import ChatResult


def test_qa_agent(monkeypatch):
    output = {
        "role": "QA",
        "task": "assess",
        "requirements_matrix": {"total": 1, "covered": ["req1"], "uncovered": []},
        "coverage": {"coverage": 1.0, "uncovered": []},
        "defect_stats": {"critical": [], "major": [], "minor": []},
        "risks": [],
        "next_steps": [],
        "sources": [],
    }

    def fake_complete(system, user, model=None, **kwargs):
        return ChatResult(content=json.dumps(output), raw={})

    monkeypatch.setattr("core.agents.qa_agent.complete", fake_complete)
    agent = QAAgent("gpt")
    res = agent.run("assess", ["req1"], ["req1 test"], [])
    assert res["coverage"]["coverage"] == 1.0
    assert res["requirements_matrix"]["total"] == 1
