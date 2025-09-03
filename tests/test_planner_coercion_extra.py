from unittest.mock import Mock, patch

import pytest

from core.orchestrator import _coerce_and_fill, generate_plan
from core.engine.executor import run_tasks
from utils import knowledge_store as ks


@patch("core.orchestrator.complete")
def test_array_root_response_wrapped(mock_complete, monkeypatch):
    mock_complete.return_value = Mock(
        content='[{"id":"1","title":"A","summary":"Build","description":"Build","role":"CTO"}]'
    )
    monkeypatch.setattr("core.orchestrator.select_model", lambda *a, **k: "test")
    tasks = generate_plan("idea")
    assert tasks[0]["id"] == "1"


def test_missing_description_or_role_backfilled():
    data = {"tasks": [{"title": "A", "summary": "B"}]}
    norm = _coerce_and_fill(data)
    t = norm["tasks"][0]
    assert t["description"] == "B"
    assert t["role"] == "Dynamic Specialist"


def test_numeric_id_preserved():
    data = {"tasks": [{"id": "2", "title": "A", "summary": "B", "description": "B", "role": "CTO"}]}
    norm = _coerce_and_fill(data)
    assert norm["tasks"][0]["id"] == "2"


@patch("core.orchestrator.complete")
def test_planner_error_raises(mock_complete, monkeypatch):
    mock_complete.return_value = Mock(content='{"error":"MISSING_INFO"}')
    monkeypatch.setattr("core.orchestrator.select_model", lambda *a, **k: "test")
    with pytest.raises(ValueError, match="planner.error_returned"):
        generate_plan("idea")


def test_executor_zero_tasks():
    out = run_tasks([], object())
    assert out == {"executed": [], "pending": []}


def test_knowledge_store_init(tmp_path, monkeypatch):
    monkeypatch.setattr(ks, "ROOT", tmp_path / "k")
    monkeypatch.setattr(ks, "UPLOADS", ks.ROOT / "uploads")
    monkeypatch.setattr(ks, "META", ks.ROOT / "meta.json")
    ks.init_store()
    assert ks.META.exists()
