from core.agents.unified_registry import resolve_model


def test_pro_profile_uses_o3(monkeypatch):
    monkeypatch.setenv("DRRD_PROFILE", "pro")
    # Exec defaults
    assert resolve_model("Research Scientist") == "o3-deep-research"
    # Plan stage
    assert resolve_model("Planner", "plan") == "o3-deep-research"
    # Synth stage
    assert resolve_model("Synthesizer", "synth") == "o3-deep-research"
