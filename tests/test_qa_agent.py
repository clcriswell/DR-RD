import json

import json

from core.agents.qa_agent import QAAgent
from core.llm import ChatResult


def test_qa_agent(monkeypatch):
    output = {
        "role": "QA",
        "task": "assess",
        "summary": "done",
        "findings": "All tests covered.",
        "defects": [],
        "coverage": "",
        "risks": [],
        "next_steps": [],
        "sources": [],
    }

    def fake_complete(system, user, model=None, **kwargs):
        return ChatResult(content=json.dumps(output), raw={})

    monkeypatch.setattr("core.agents.qa_agent.complete", fake_complete)
    agent = QAAgent("gpt")
    res = agent.run("assess", ["req1"], ["req1 test"], [], context="")
    assert res["findings"].startswith("All")


def test_qa_agent_dict_task(monkeypatch):
    output = {
        "role": "QA",
        "task": "assess",
        "summary": "done",
        "findings": "All tests covered.",
        "defects": [],
        "coverage": "",
        "risks": [],
        "next_steps": [],
        "sources": [],
    }

    def fake_complete(system, user, model=None, **kwargs):
        return ChatResult(content=json.dumps(output), raw={})

    monkeypatch.setattr("core.agents.qa_agent.complete", fake_complete)
    agent = QAAgent("gpt")
    res = agent.run({"brief": "assess"}, ["req1"], ["req1 test"], [], context="")
    assert res["findings"].startswith("All")
