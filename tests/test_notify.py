import urllib.request

import utils.notify as notify


def test_format_plain_redacts():
    note = notify.Note(
        event="run_completed",
        run_id="r1",
        status="success",
        mode="m",
        idea_preview="secret sk-123456789012345678901234",
    )
    out = notify._format_plain(note)
    assert "sk-12345" not in out


def test_dispatch_missing_secrets(monkeypatch):
    note = notify.Note(
        event="run_completed",
        run_id="r1",
        status="success",
        mode="m",
        idea_preview="x",
    )
    monkeypatch.setattr(notify, "get_secret", lambda k: None)
    prefs = {
        "notifications": {
            "enabled": True,
            "channels": ["slack", "email", "webhook"],
            "email_to": ["a@example.com"],
            "slack_mention": "",
            "events": {"run_completed": True},
        }
    }
    res = notify.dispatch(note, prefs)
    assert res == {"slack": False, "email": False, "webhook": False}


def test_webhook_hmac_header(monkeypatch):
    captured = {}

    class Dummy:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def fake_urlopen(req, timeout=5):
        captured["headers"] = dict(req.header_items())
        captured["data"] = req.data
        return Dummy()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    secrets = {"WEBHOOK_URL": "http://example.com", "WEBHOOK_SECRET": "abc"}
    monkeypatch.setattr(notify, "get_secret", lambda k: secrets.get(k))
    note = notify.Note(
        event="run_completed",
        run_id="r1",
        status="success",
        mode="m",
        idea_preview="x",
    )
    assert notify._webhook_send(note) is True
    assert any(k.lower() == "x-drrd-signature" for k in captured["headers"])
