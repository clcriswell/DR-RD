import json
import hmac
import hashlib
import time
import os
from fastapi.testclient import TestClient
from dr_rd.integrations.server import create_app


def _sig(secret: str, ts: str, body: str) -> str:
    basestring = f"v0:{ts}:{body}"
    return "v0=" + hmac.new(secret.encode(), basestring.encode(), hashlib.sha256).hexdigest()


def test_slack_signature_and_command(monkeypatch):
    secret = "test"
    os.environ["SLACK_SIGNING_SECRET"] = secret
    called = {}

    def fake(role, title, desc, inputs):
        called["args"] = (role, title)
        return {"role": role, "output": "ok"}

    monkeypatch.setattr("core.runner.execute_task", fake)
    app = create_app()
    client = TestClient(app)
    body = json.dumps({"text": "run Research \"Ping\""})
    ts = str(int(time.time()))
    sig = _sig(secret, ts, body)
    resp = client.post("/slack/events", data=body, headers={
        "X-Slack-Request-Timestamp": ts,
        "X-Slack-Signature": sig,
    })
    assert resp.status_code == 200
    assert called["args"] == ("Research", "Ping")
    data = resp.json()
    assert data["ok"] is True
    assert data["result"]["role"] == "Research"
