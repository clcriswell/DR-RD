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
@patch("dr_rd.utils.llm_client.llm_call")
def test_rag_included_when_enabled(mock_llm, monkeypatch):
    mock_llm.return_value = make_openai_response("ok")
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_TOPK", "2")
    import config.feature_flags as ff
    importlib.reload(ff)
    import agents.base_agent as ba
    importlib.reload(ba)
    agent = ba.BaseAgent("Test", "gpt-5", "sys", "Task: {task}", retriever=StubRetriever())
    agent.run("idea", "do something")
    prompt = mock_llm.call_args.kwargs["messages"][1]["content"]
    assert "# RAG Knowledge" in prompt
    assert "alpha data" in prompt
    assert "(alpha.txt)" in prompt


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("dr_rd.utils.llm_client.llm_call")
def test_rag_skipped_when_disabled(mock_llm, monkeypatch):
    mock_llm.return_value = make_openai_response("ok")
    monkeypatch.setenv("RAG_ENABLED", "false")
    import config.feature_flags as ff
    importlib.reload(ff)
    import agents.base_agent as ba
    importlib.reload(ba)
    agent = ba.BaseAgent("Test", "gpt-5", "sys", "Task: {task}", retriever=StubRetriever())
    agent.run("idea", "do something")
    prompt = mock_llm.call_args.kwargs["messages"][1]["content"]
    assert "# RAG Knowledge" not in prompt


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
@patch("dr_rd.utils.llm_client.llm_call")
def test_rag_snippet_not_truncated(mock_llm, monkeypatch):
    mock_llm.return_value = make_openai_response("ok")
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_TOPK", "1")

    class LongRetriever:
        def query(self, text: str, top_k: int):
            return [("one two three four five", "doc.txt")]

    import config.feature_flags as ff
    importlib.reload(ff)
    import agents.base_agent as ba
    importlib.reload(ba)
    agent = ba.BaseAgent("Test", "gpt-5", "sys", "Task: {task}", retriever=LongRetriever())
    agent.run("idea", "do something")
    prompt = mock_llm.call_args.kwargs["messages"][1]["content"]
    assert "one two three four five" in prompt
