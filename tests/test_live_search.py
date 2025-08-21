import types
import importlib

import config.feature_flags as ff
import core.agents.base_agent as ba
import core.agents.ip_analyst_agent as ip_agent


class DummyResp:
    def __init__(self, content: str):
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=content), usage=None)]


def test_live_search_triggered(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_SEARCH", "true")
    importlib.reload(ff)
    importlib.reload(ba)
    importlib.reload(ip_agent)

    def fake_search(role, idea, q, k=5):
        return [{"snippet": "alpha beta", "title": "T1", "link": "u1"}]

    monkeypatch.setattr("utils.search_tools.search_google", fake_search)
    monkeypatch.setattr("utils.search_tools.call_openai", lambda *a, **k: {"text": "summary"})

    captured = {}

    def fake_agent_llm(model, messages, **params):
        captured["prompt"] = messages[1]["content"]
        return {
            "text": '{"role":"IP Analyst","task":"x","findings":[],"risks":[],"next_steps":[]}',
            "raw": DummyResp(""),
        }

    monkeypatch.setattr(ip_agent, "call_openai", fake_agent_llm)
    agent = ip_agent.IPAnalystAgent(model="gpt-5", retriever=None)
    out = agent.act("idea", "task")
    assert "# Web Search Results" in captured["prompt"]
    assert out["sources"] == ["T1"]


def test_no_live_search_with_rag(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_SEARCH", "true")
    monkeypatch.setenv("RAG_ENABLED", "true")
    importlib.reload(ff)
    importlib.reload(ba)
    importlib.reload(ip_agent)
    called = {"search": False}

    def fake_search(role, idea, q, k=5):
        called["search"] = True
        return []

    monkeypatch.setattr("utils.search_tools.search_google", fake_search)
    monkeypatch.setattr("utils.search_tools.call_openai", lambda *a, **k: {"text": "summary"})

    captured = {}

    def fake_agent_llm(model, messages, **params):
        captured["prompt"] = messages[1]["content"]
        return {
            "text": '{"role":"IP Analyst","task":"x","findings":[],"risks":[],"next_steps":[]}',
            "raw": DummyResp(""),
        }

    monkeypatch.setattr(ip_agent, "call_openai", fake_agent_llm)

    class DummyRetriever:
        def query(self, q, k):
            return [("word " * 60, "Doc1")]

    agent = ip_agent.IPAnalystAgent(model="gpt-5", retriever=DummyRetriever())
    agent.act("idea", "task")
    assert "# Web Search Results" not in captured.get("prompt", "")
    assert called["search"] is False


def test_live_search_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_SEARCH", "false")
    importlib.reload(ff)
    importlib.reload(ba)
    importlib.reload(ip_agent)
    called = {"search": False}

    def fake_search(role, idea, q, k=5):
        called["search"] = True
        return []

    monkeypatch.setattr("utils.search_tools.search_google", fake_search)
    monkeypatch.setattr("utils.search_tools.call_openai", lambda *a, **k: {"text": "summary"})

    captured = {}

    def fake_agent_llm(model, messages, **params):
        captured["prompt"] = messages[1]["content"]
        return {
            "text": '{"role":"IP Analyst","task":"x","findings":[],"risks":[],"next_steps":[]}',
            "raw": DummyResp(""),
        }

    monkeypatch.setattr(ip_agent, "call_openai", fake_agent_llm)
    agent = ip_agent.IPAnalystAgent(model="gpt-5", retriever=None)
    agent.act("idea", "task")
    assert "# Web Search Results" not in captured.get("prompt", "")
    assert called["search"] is False
