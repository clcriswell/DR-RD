import pytest

from core.llm import select_model


def test_select_model_precedence(monkeypatch):
    monkeypatch.delenv("DRRD_FORCE_MODEL", raising=False)
    monkeypatch.delenv("DRRD_MODEL_AGENT_SYNTHESIZER", raising=False)
    monkeypatch.delenv("DRRD_MODEL_PLANNER", raising=False)
    monkeypatch.delenv("DRRD_OPENAI_MODEL", raising=False)
    # UI wins
    assert select_model("planner", "ui", agent_name="Synthesizer") == "ui"
    # Per-agent env
    monkeypatch.setenv("DRRD_MODEL_AGENT_SYNTHESIZER", "agent-env")
    assert select_model("agent", None, agent_name="Synthesizer") == "agent-env"
    monkeypatch.delenv("DRRD_MODEL_AGENT_SYNTHESIZER", raising=False)
    # Purpose env
    monkeypatch.setenv("DRRD_MODEL_AGENT", "purpose-env")
    assert select_model("agent", None) == "purpose-env"
    monkeypatch.delenv("DRRD_MODEL_AGENT", raising=False)
    # Global env
    monkeypatch.setenv("DRRD_OPENAI_MODEL", "global-env")
    assert select_model("agent", None) == "global-env"


def test_select_model_forced_override(monkeypatch):
    monkeypatch.setenv("DRRD_FORCE_MODEL", "forced")
    assert select_model("planner", "ui-choice") == "forced"
