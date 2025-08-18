from unittest.mock import Mock, patch
import importlib
import os


class StubRetriever:
    def query(self, text: str, top_k: int):
        return [("alpha data", "alpha.txt"), ("beta info", "beta.txt")]


def make_openai_response(text: str):
    choice = Mock()
    choice.message = Mock(content=text)
    return Mock(choices=[choice])


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("openai.chat.completions.create")
def test_rag_included_when_enabled(mock_create, monkeypatch):
    mock_create.return_value = make_openai_response("ok")
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_TOPK", "2")
    import config.feature_flags as ff
    importlib.reload(ff)
    import agents.base_agent as ba
    importlib.reload(ba)
    agent = ba.BaseAgent("Test", "gpt-4o", "sys", "Task: {task}", retriever=StubRetriever())
    agent.run("idea", "do something")
    prompt = mock_create.call_args.kwargs["messages"][1]["content"]
    assert "# RAG Knowledge" in prompt
    assert "alpha data" in prompt
    assert "(alpha.txt)" in prompt


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("openai.chat.completions.create")
def test_rag_skipped_when_disabled(mock_create, monkeypatch):
    mock_create.return_value = make_openai_response("ok")
    monkeypatch.setenv("RAG_ENABLED", "false")
    import config.feature_flags as ff
    importlib.reload(ff)
    import agents.base_agent as ba
    importlib.reload(ba)
    agent = ba.BaseAgent("Test", "gpt-4o", "sys", "Task: {task}", retriever=StubRetriever())
    agent.run("idea", "do something")
    prompt = mock_create.call_args.kwargs["messages"][1]["content"]
    assert "# RAG Knowledge" not in prompt


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("openai.chat.completions.create")
def test_rag_snippet_token_truncation(mock_create, monkeypatch):
    mock_create.return_value = make_openai_response("ok")
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_TOPK", "1")
    monkeypatch.setenv("RAG_SNIPPET_TOKENS", "3")

    class LongRetriever:
        def query(self, text: str, top_k: int):
            return [("one two three four five", "doc.txt")]

    import config.feature_flags as ff
    importlib.reload(ff)
    import agents.base_agent as ba
    importlib.reload(ba)
    agent = ba.BaseAgent("Test", "gpt-4o", "sys", "Task: {task}", retriever=LongRetriever())
    agent.run("idea", "do something")
    prompt = mock_create.call_args.kwargs["messages"][1]["content"]
    assert "one two three" in prompt
    assert "four" not in prompt
