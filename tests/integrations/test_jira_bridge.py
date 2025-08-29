import os
from fastapi.testclient import TestClient
from dr_rd.integrations.server import create_app


def test_jira_issue(monkeypatch):
    os.environ.update({
        "JIRA_BASE_URL": "https://jira.example.com",
        "JIRA_EMAIL": "user@example.com",
        "JIRA_API_TOKEN": "token",
        "JIRA_PROJECT_KEY": "DRRD",
    })
    captured = {}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"key": "DRRD-1"}

    def fake_post(url, json, auth):
        captured["url"] = url
        captured["json"] = json
        captured["auth"] = auth
        return FakeResp()

    monkeypatch.setattr("requests.post", fake_post)
    app = create_app()
    client = TestClient(app)
    resp = client.post("/jira/hook", json={"summary": "Ping", "description": "hi"})
    assert resp.status_code == 200
    assert captured["json"]["fields"]["summary"] == "Ping"
    assert captured["auth"] == ("user@example.com", "token")
    assert resp.json()["key"] == "DRRD-1"
