from core.graph.state import GraphState, GraphTask
from core.graph import nodes
from core.retrieval import query_builder, rag, live_search
import core.router as router
import config.feature_flags as ff


def test_retrieval_node_passes_context(monkeypatch):
    ff.RAG_ENABLED = True
    ff.ENABLE_LIVE_SEARCH = False

    state = GraphState(
        idea="idea",
        constraints=[],
        risk_posture="low",
        tasks=[GraphTask(id="T1", title="t", description="d")],
        cursor=0,
        answers={},
        trace=[],
        tool_trace=[],
        retrieved={},
    )

    monkeypatch.setattr(query_builder, "build_queries", lambda *a, **k: ["q1"])
    monkeypatch.setattr(rag, "rag_search", lambda q, k: [{"url": "u", "text": "t", "title": "u"}])
    monkeypatch.setattr(live_search, "live_search", lambda q, caps: [])

    captured = {}

    def fake_dispatch(task, ui_model=None):
        captured["task"] = task
        return {"content": "ok"}

    monkeypatch.setattr(router, "dispatch", fake_dispatch)

    nodes.retrieval_node(state)
    nodes.agent_node(state)

    assert state.answers["T1"]["retrieval_sources"]
    assert "context" in captured["task"]
