import json
from types import SimpleNamespace

import pytest

from core.llm import ChatResult
from core import orchestrator
from core.orchestrator import generate_plan


def _patch_streamlit(monkeypatch):
    monkeypatch.setattr(orchestrator, "st", SimpleNamespace(session_state={}))


def _patch_redaction(monkeypatch):
    monkeypatch.setattr(orchestrator, "load_redaction_policy", lambda: {})
    monkeypatch.setattr(orchestrator, "redact_text", lambda policy, txt: txt)


def test_rehydration_before_validation(monkeypatch):
    _patch_streamlit(monkeypatch)
    _patch_redaction(monkeypatch)
    monkeypatch.setenv("DRRD_PSEUDONYMIZE_TO_MODEL", "1")

    def fake_complete(system, user, *, model, response_format):
        payload = {
            "tasks": [
                {
                    "id": "T01",
                    "role": "Role",
                    "title": "Meet [PERSON_1] at [ORG_1]",
                    "summary": "Email [EMAIL_1]",
                }
            ]
        }
        return ChatResult(content=json.dumps(payload), raw=payload)

    monkeypatch.setattr(orchestrator, "complete", fake_complete)
    tasks = generate_plan(
        "Alice Smith from Acme Corp, contact alice@acme.com",
        ui_model="x",
    )
    assert "Alice Smith" in tasks[0]["title"]
    assert "Acme Corp" in tasks[0]["title"]
    assert "alice@acme.com" in tasks[0]["description"]
    monkeypatch.delenv("DRRD_PSEUDONYMIZE_TO_MODEL", raising=False)


def test_missing_ids_injected(monkeypatch, caplog):
    _patch_streamlit(monkeypatch)
    _patch_redaction(monkeypatch)

    def fake_complete(system, user, *, model, response_format):
        payload = {
            "tasks": [
                {"role": "Role", "title": "Task", "summary": "One"},
                {"id": "T09", "role": "Role2", "title": "Task2", "summary": "Two"},
            ]
        }
        return ChatResult(content=json.dumps(payload), raw=payload)

    monkeypatch.setattr(orchestrator, "complete", fake_complete)
    with caplog.at_level("INFO"):
        tasks = generate_plan("idea", ui_model="x")
    assert len(tasks) == 2
    assert any("injected" in r.message for r in caplog.records)


def test_description_field_rejected(monkeypatch):
    _patch_streamlit(monkeypatch)
    _patch_redaction(monkeypatch)

    def bad_complete(system, user, *, model, response_format):
        payload = {"tasks": [{"id": "T01", "role": "R", "title": "T", "description": "D"}]}
        return ChatResult(content=json.dumps(payload), raw=payload)

    monkeypatch.setattr(orchestrator, "complete", bad_complete)
    tasks = generate_plan("idea", ui_model="x")
    assert tasks == []
