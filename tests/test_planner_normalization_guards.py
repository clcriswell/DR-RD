import json
from types import SimpleNamespace

import pytest

from core import orchestrator
from core.orchestrator import _coerce_and_fill, generate_plan
from core.schemas import Plan
from core.llm import ChatResult


def _patch_streamlit(monkeypatch):
    monkeypatch.setattr(orchestrator, "st", SimpleNamespace(session_state={}))


def _patch_redaction(monkeypatch):
    monkeypatch.setattr(orchestrator, "load_redaction_policy", lambda: {})
    monkeypatch.setattr(orchestrator, "redact_text", lambda policy, txt: txt)


def test_shape_repair_array_root():
    tasks = [
        {"id": "T01", "title": "A", "summary": "B", "description": "B", "role": "CTO"}
    ]
    data = _coerce_and_fill({"tasks": tasks})
    Plan.model_validate(data, strict=True)
    assert data["tasks"][0]["id"] == "T01"


def test_backfill_fields():
    raw = {
        "tasks": [
            {"id": "1", "title": "A", "summary": "S", "role": "CTO"},
            {"id": "2", "title": "B", "description": "D", "role": "CTO"},
        ]
    }
    data = _coerce_and_fill(raw)
    assert data["tasks"][0]["description"] == "S"
    assert data["tasks"][1]["summary"] == "D"


def test_id_and_role_coercion():
    raw = {
        "tasks": [
            {"id": 5, "title": "A", "summary": "S", "description": "S"},
            {
                "id": "DEV_2",
                "title": "B",
                "summary": "S",
                "description": "S",
                "role": "",
            },
        ]
    }
    data = _coerce_and_fill(raw)
    Plan.model_validate(data, strict=True)
    ids = [t["id"] for t in data["tasks"]]
    roles = [t["role"] for t in data["tasks"]]
    assert ids == ["5", "DEV_2"]
    assert roles == ["Dynamic Specialist", "Dynamic Specialist"]


def test_normalization_zero_failfast(monkeypatch, tmp_path):
    _patch_streamlit(monkeypatch)
    _patch_redaction(monkeypatch)

    def fake_complete(system, user, *, model, response_format):
        payload = {"tasks": [{"id": "T01", "role": "CTO"}]}
        return ChatResult(content=json.dumps(payload), raw=payload)

    monkeypatch.setattr(orchestrator, "complete", fake_complete)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError) as exc:
        generate_plan("idea", ui_model="x")
    assert "planner.normalization_zero" in str(exc.value)
    logs = list((tmp_path / "debug" / "logs").glob("planner_payload_*.json"))
    assert logs
