from utils import providers


def test_has_secrets_false(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert providers.has_secrets("openai") is False


def test_defaults_and_snapshot():
    prov, model = providers.default_model_for_mode("standard")
    assert prov == "openai" and model == "gpt-4o-mini"
    snap = providers.to_prefs_snapshot(prov, model)
    assert providers.from_prefs_snapshot(snap) == (prov, model)
