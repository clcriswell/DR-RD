import logging

from app.config_loader import load_profile


def test_env_mode_deprecated(monkeypatch, caplog):
    monkeypatch.setenv("DRRD_MODE", "legacy")
    with caplog.at_level(logging.WARNING):
        cfg, _ = load_profile()
    assert "DRRD_MODE 'legacy' is deprecated" in caplog.text
    assert cfg.get("target_cost_usd") == 2.50
