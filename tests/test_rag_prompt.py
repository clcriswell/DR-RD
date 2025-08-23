import importlib
import os
from unittest.mock import Mock, patch

from dr_rd.retrieval.vector_store import Snippet


class StubRetriever:
    def query(self, text: str, top_k: int):
        return [
            Snippet(text="alpha data", source="alpha.txt"),
            Snippet(text="beta info", source="beta.txt"),
        ]


def make_openai_response(text: str):
    choice = Mock()
    choice.message = Mock(content=text)
    return Mock(choices=[choice])


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("core.llm_client.call_openai")
def test_rag_included_when_enabled(mock_llm, monkeypatch):
    mock_llm.return_value = {"text": "ok", "raw": make_openai_response("ok")}
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_TOPK", "2")
    import config.feature_flags as ff

    importlib.reload(ff)
    import core.agents.base_agent as ba

    importlib.reload(ba)
    agent = ba.BaseAgent(
        "Test", "gpt-5", "sys", "Task: {task}", retriever=StubRetriever()
    )
    agent.run("idea", "do something")
    prompt = mock_llm.call_args.kwargs["messages"][1]["content"]
    assert "# RAG Knowledge" in prompt
    assert "alpha data" in prompt


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("core.llm_client.call_openai")
def test_rag_skipped_when_disabled(mock_llm, monkeypatch):
    mock_llm.return_value = {"text": "ok", "raw": make_openai_response("ok")}
    monkeypatch.setenv("RAG_ENABLED", "false")
    import config.feature_flags as ff

    importlib.reload(ff)
    import core.agents.base_agent as ba

    importlib.reload(ba)
    agent = ba.BaseAgent(
        "Test", "gpt-5", "sys", "Task: {task}", retriever=StubRetriever()
    )
    agent.run("idea", "do something")
    prompt = mock_llm.call_args.kwargs["messages"][1]["content"]
    assert "# RAG Knowledge" not in prompt


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("core.llm_client.call_openai")
def test_rag_snippet_not_truncated(mock_llm, monkeypatch):
    mock_llm.return_value = {"text": "ok", "raw": make_openai_response("ok")}
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_TOPK", "1")

    class LongRetriever:
        def query(self, text: str, top_k: int):
            return [Snippet(text="one two three four five", source="doc.txt")]

    import config.feature_flags as ff

    importlib.reload(ff)
    import core.agents.base_agent as ba

    importlib.reload(ba)
    agent = ba.BaseAgent(
        "Test", "gpt-5", "sys", "Task: {task}", retriever=LongRetriever()
    )
    agent.run("idea", "do something")
    prompt = mock_llm.call_args.kwargs["messages"][1]["content"]
    assert "one two three four five" in prompt
