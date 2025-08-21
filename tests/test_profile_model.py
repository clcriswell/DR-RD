from core.agents.unified_registry import resolve_model


def test_pro_profile_uses_gpt5(monkeypatch):
    monkeypatch.setenv("DRRD_PROFILE", "pro")
    # Exec defaults
    assert resolve_model("Research Scientist") == "gpt-5"
    # Plan stage
    assert resolve_model("Planner", "plan") == "gpt-5"
    # Synth stage
    assert resolve_model("Synthesizer", "synth") == "gpt-5"


def test_test_profile_defaults_to_gpt4turbo(monkeypatch):
    monkeypatch.setenv("DRRD_PROFILE", "test")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("DRRD_MODEL_EXEC_TEST", raising=False)
    assert resolve_model("Research Scientist") == "gpt-4-turbo"


def test_openai_model_override(monkeypatch):
    monkeypatch.setenv("DRRD_PROFILE", "test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.delenv("DRRD_MODEL_EXEC_TEST", raising=False)
    assert resolve_model("Research Scientist") == "gpt-4o-mini"
