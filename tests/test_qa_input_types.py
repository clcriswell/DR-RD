import json

from core.agents.qa_agent import QAAgent
from core.llm import ChatResult


def fake_complete(system, user, model=None, **kwargs):
    output = {
        "role": "QA",
        "task": "assess",
        "requirements_matrix": {"total": 0, "covered": [], "uncovered": []},
        "coverage": {"coverage": 0.0, "uncovered": []},
        "defect_stats": {"critical": [], "major": [], "minor": []},
        "risks": [],
        "next_steps": [],
        "sources": [],
    }
    return ChatResult(content=json.dumps(output), raw={})


def test_qa_accepts_str(monkeypatch):
    monkeypatch.setattr("core.agents.qa_agent.complete", fake_complete)
    agent = QAAgent("gpt")
    res = agent.run("task", ["r"], ["t"], [])
    assert res["role"] == "QA"


def test_qa_accepts_dict(monkeypatch):
    monkeypatch.setattr("core.agents.qa_agent.complete", fake_complete)
    agent = QAAgent("gpt")
    res = agent.run({"brief": "task"}, ["r"], ["t"], [])
    assert res["role"] == "QA"

