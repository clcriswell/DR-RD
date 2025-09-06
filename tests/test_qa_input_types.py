import json

from core.agents.qa_agent import QAAgent
from core.llm import ChatResult


def fake_complete(system, user, model=None, **kwargs):
    output = {
        "role": "QA",
        "task": "assess",
        "summary": "done",
        "findings": "none",
        "defects": [],
        "coverage": "",
        "risks": [],
        "next_steps": [],
        "sources": [],
    }
    return ChatResult(content=json.dumps(output), raw={})


def test_qa_accepts_str(monkeypatch):
    monkeypatch.setattr("core.agents.qa_agent.complete", fake_complete)
    agent = QAAgent("gpt")
    res = agent.run("task", ["r"], ["t"], [], context="")
    assert res["findings"] == "none"


def test_qa_accepts_dict(monkeypatch):
    monkeypatch.setattr("core.agents.qa_agent.complete", fake_complete)
    agent = QAAgent("gpt")
    res = agent.run({"brief": "task"}, ["r"], ["t"], [], context="")
    assert res["findings"] == "none"

