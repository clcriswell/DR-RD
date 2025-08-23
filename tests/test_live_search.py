import types
import importlib
import types

import config.feature_flags as ff
import core.agents.base_agent as ba
import core.agents.ip_analyst_agent as ip_agent
from dr_rd.retrieval.vector_store import Snippet
from dr_rd.retrieval.live_search import OpenAIWebSearchClient, Source


class DummyResp:
    def __init__(self, content: str):
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=content), usage=None)]


def test_live_search_triggered(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_SEARCH", "true")
    importlib.reload(ff)
    importlib.reload(ba)
    importlib.reload(ip_agent)
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = rbudget.RetrievalBudget(3)

    def fake_search_and_summarize(query, k, max_tokens):
        return "summary", [Source(title="T1", url="u1")]

    monkeypatch.setattr(
        OpenAIWebSearchClient, "search_and_summarize", staticmethod(fake_search_and_summarize)
    )

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
    for mod in (ff, ba, ip_agent):
        monkeypatch.setattr(mod, "VECTOR_INDEX_PRESENT", True, raising=False)
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = rbudget.RetrievalBudget(3)
    called = {"search": False}

    def fake_search_and_summarize(query, k, max_tokens):
        called["search"] = True
        return "", []

    monkeypatch.setattr(
        OpenAIWebSearchClient, "search_and_summarize", staticmethod(fake_search_and_summarize)
    )

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
            return [Snippet(text="word " * 60, source="Doc1")]

    agent = ip_agent.IPAnalystAgent(model="gpt-5", retriever=DummyRetriever())
    agent.act("idea", "task")
    assert "# Web Search Results" not in captured.get("prompt", "")
    assert called["search"] is False


def test_live_search_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_SEARCH", "false")
    importlib.reload(ff)
    importlib.reload(ba)
    importlib.reload(ip_agent)
    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = rbudget.RetrievalBudget(3)
    called = {"search": False}

    def fake_search_and_summarize(query, k, max_tokens):
        called["search"] = True
        return "", []

    monkeypatch.setattr(
        OpenAIWebSearchClient, "search_and_summarize", staticmethod(fake_search_and_summarize)
    )

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
