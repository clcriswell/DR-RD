import json
from types import SimpleNamespace

import pytest

from core import orchestrator
from core.llm import ChatResult
from core.orchestrator import generate_plan


def _patch_streamlit(monkeypatch):
    monkeypatch.setattr(orchestrator, "st", SimpleNamespace(session_state={}))


def _patch_redaction(monkeypatch):
    monkeypatch.setattr(orchestrator, "load_redaction_policy", lambda: {})
    monkeypatch.setattr(orchestrator, "redact_text", lambda policy, txt: txt)


def test_normalizer_injects_ids(monkeypatch, caplog):
    _patch_streamlit(monkeypatch)
    _patch_redaction(monkeypatch)

    def fake_complete(system, user, *, model, response_format):
        payload = {
            "tasks": [
                {
                    "role": "Role",
                    "title": "Task",
                    "summary": "Done",
                    "description": "Desc",
                }
            ]
        }
        return ChatResult(content=json.dumps(payload), raw=payload)

    monkeypatch.setattr(orchestrator, "complete", fake_complete)
    with caplog.at_level("INFO"):
        tasks = generate_plan("idea", ui_model="x")
    assert tasks and tasks[0]["role"] == "Role"
    assert any("injected" in r.message for r in caplog.records)


def test_schema_violation(monkeypatch):
    _patch_streamlit(monkeypatch)
    _patch_redaction(monkeypatch)

    def bad_complete(system, user, *, model, response_format):
        payload = {"tasks": [{"id": "T01", "role": "Role", "title": "Task"}]}
        return ChatResult(content=json.dumps(payload), raw=payload)

    monkeypatch.setattr(orchestrator, "complete", bad_complete)
    with pytest.raises(ValueError) as exc:
        generate_plan("idea", ui_model="x")
    assert "missing" in str(exc.value)
