from core.agents.unified_registry import resolve_model


def test_pro_profile_uses_gpt5(monkeypatch):
    monkeypatch.setenv("DRRD_PROFILE", "pro")
    assert resolve_model("Research Scientist") == "gpt-5"
    assert resolve_model("Planner", "plan") == "gpt-5"
    assert resolve_model("Synthesizer", "synth") == "gpt-5"


def test_test_profile_maps_to_standard(monkeypatch, caplog):
    monkeypatch.setenv("DRRD_PROFILE", "test")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    with caplog.at_level("WARNING"):
        model = resolve_model("Research Scientist")
    assert model == "gpt-4.1-mini"
    assert any("deprecated" in r.message for r in caplog.records)


def test_openai_model_override(monkeypatch):
    monkeypatch.setenv("DRRD_PROFILE", "standard")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    assert resolve_model("Research Scientist") == "gpt-4o-mini"
