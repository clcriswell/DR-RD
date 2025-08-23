import logging
from types import SimpleNamespace
from unittest.mock import patch

import config.feature_flags as ff
from core.agents import planner_agent
from core.retrieval.budget import RetrievalBudget
from dr_rd.retrieval import pipeline
from dr_rd.retrieval.live_search import Source


class DummyClient:
    def __init__(self):
        self.called = 0

    def search_and_summarize(self, query, k, max_tokens):
        self.called += 1
        return "s1\ns2", [
            Source(title="t1", url="u1"),
            Source(title="t2", url="u2"),
            Source(title="t3", url="u3"),
        ]


def test_planner_web_fallback(monkeypatch, caplog):
    # Configure flags for web-only retrieval
    for mod in (ff, planner_agent):
        monkeypatch.setattr(mod, "VECTOR_INDEX_PRESENT", False, raising=False)
        monkeypatch.setattr(mod, "ENABLE_LIVE_SEARCH", True, raising=False)
        monkeypatch.setattr(mod, "LIVE_SEARCH_BACKEND", "openai", raising=False)
        monkeypatch.setattr(mod, "RAG_ENABLED", True, raising=False)
        monkeypatch.setattr(mod, "RAG_TOPK", 5, raising=False)

    from core.retrieval import budget as rbudget

    rbudget.RETRIEVAL_BUDGET = RetrievalBudget(1)

    dummy = DummyClient()
    monkeypatch.setattr("dr_rd.retrieval.context.get_live_client", lambda _b: dummy)

    def fake_llm_call(_a, _b, _c, messages, **_kw):
        return SimpleNamespace(
            output_text="{}",
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    usage=SimpleNamespace(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                )
            ],
        )

    with caplog.at_level(logging.INFO):
        with patch("core.agents.planner_agent.llm_call", fake_llm_call), patch(
            "core.agents.planner_agent.extract_planner_payload", return_value={}
        ):
            planner_agent.run_planner("idea", "model")

    assert dummy.called == 1
    assert rbudget.RETRIEVAL_BUDGET.used == 1
    assert any(
        "RetrievalTrace agent=Planner" in r.message
        and "web_used=true" in r.message
        and "reason=web_only_mode" in r.message
        for r in caplog.records
    )
