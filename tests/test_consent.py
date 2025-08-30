from utils import consent, telemetry


def test_set_and_get_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(consent, "CONSENT_PATH", tmp_path / "consent.json")
    assert consent.get() is None
    c = consent.set(telemetry=True, surveys=False)
    assert c.telemetry and not c.surveys
    loaded = consent.get()
    assert loaded == c


def test_telemetry_respects_consent(tmp_path, monkeypatch):
    monkeypatch.setattr(consent, "CONSENT_PATH", tmp_path / "consent.json")
    monkeypatch.setattr(telemetry, "LOG_DIR", tmp_path / "tel")
    telemetry.LOG_DIR.mkdir(parents=True, exist_ok=True)
    # No consent yet -> no file written
    telemetry.log_event({"event": "x"})
    assert not list(telemetry.LOG_DIR.glob("events-*"))
    consent.set(telemetry=True, surveys=True)
    telemetry.log_event({"event": "y"})
    assert list(telemetry.LOG_DIR.glob("events-*"))

