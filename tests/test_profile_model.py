from core.agents.unified_registry import resolve_model


def test_openai_model_override(monkeypatch):
    monkeypatch.setenv("DRRD_PROFILE", "standard")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    assert resolve_model("Research Scientist") == "gpt-4o-mini"
