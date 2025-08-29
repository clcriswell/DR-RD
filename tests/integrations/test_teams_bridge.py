import os
from fastapi.testclient import TestClient
from dr_rd.integrations.server import create_app


def test_teams_allowed_and_denied(monkeypatch):
    os.environ["TEAMS_ALLOWED_COMMANDS"] = "run"
    called = {}

    def fake(role, title, desc, inputs):
        called["args"] = (role, title)
        return {"role": role, "output": "ok"}

    monkeypatch.setattr("core.runner.execute_task", fake)
    app = create_app()
    client = TestClient(app)
    resp = client.post("/teams/messages", json={"text": "run Research \"Ping\""})
    assert resp.status_code == 200
    assert called["args"] == ("Research", "Ping")

    resp2 = client.post("/teams/messages", json={"text": "bad Research \"Ping\""})
    assert resp2.status_code == 403
