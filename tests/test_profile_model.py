from core.agents.unified_registry import resolve_model


def test_pro_profile_uses_gpt5(monkeypatch):
    monkeypatch.setenv("DRRD_PROFILE", "pro")
    # Exec defaults
    assert resolve_model("Research Scientist") == "gpt-5"
    # Plan stage
    assert resolve_model("Planner", "plan") == "gpt-5"
    # Synth stage
    assert resolve_model("Synthesizer", "synth") == "gpt-5"
