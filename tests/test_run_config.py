import streamlit as st

from utils.run_config import (
    RunConfig,
    defaults,
    from_session,
    to_orchestrator_kwargs,
    to_session,
)


def test_defaults():
    st.session_state.clear()
    cfg = defaults()
    assert isinstance(cfg, RunConfig)
    assert cfg.idea == ""
    assert cfg.knowledge_sources == ["samples"]
    assert cfg.budget_limit_usd is None
    assert cfg.max_tokens is None


def test_to_orchestrator_kwargs_minimal():
    st.session_state.clear()
    cfg = RunConfig(idea="x", rag_enabled=True)
    kw = to_orchestrator_kwargs(cfg)
    assert kw["idea"] == "x"
    assert kw["rag"] is True
    assert kw["knowledge_sources"] == []
    assert kw["max_tokens"] is None
    assert kw["budget_limit_usd"] is None


def test_to_orchestrator_kwargs_with_advanced():
    st.session_state.clear()
    cfg = RunConfig(idea="y", advanced={"temperature": 0.2})
    kw = to_orchestrator_kwargs(cfg)
    assert kw["temperature"] == 0.2


def test_session_roundtrip():
    st.session_state.clear()
    original = RunConfig(
        idea="idea",
        rag_enabled=True,
        knowledge_sources=["k"],
    )
    to_session(original)
    loaded = from_session()
    assert loaded == original
