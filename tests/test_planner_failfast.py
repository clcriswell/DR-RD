import json
from pathlib import Path

import pytest

import core.orchestrator as orch


class _GoodResp:
    content = json.dumps({"tasks": [{"id": "T01", "title": "CTO", "summary": "Build"}]})


def test_summary_backfilled(monkeypatch):
    monkeypatch.setattr(orch, "complete", lambda *a, **k: _GoodResp())
    monkeypatch.setattr(orch, "select_model", lambda *a, **k: "test")
    tasks = orch.generate_plan("idea")
    assert tasks[0]["description"] == "Build"


class _NoIdResp:
    content = json.dumps({"tasks": [{"title": "CTO", "summary": "Build"}]})


def test_missing_id_backfilled(monkeypatch):
    monkeypatch.setattr(orch, "complete", lambda *a, **k: _NoIdResp())
    monkeypatch.setattr(orch, "select_model", lambda *a, **k: "test")
    tasks = orch.generate_plan("idea")
    assert tasks[0]["id"].startswith("T")


class _BadResp:
    content = json.dumps({"tasks": [{"id": "T01", "title": "CTO", "summary": "ab"}]})


def test_normalization_failfast(monkeypatch):
    for p in Path("debug/logs").glob("planner_payload_*.json"):
        p.unlink()
    monkeypatch.setattr(orch, "complete", lambda *a, **k: _BadResp())
    monkeypatch.setattr(orch, "select_model", lambda *a, **k: "test")
    with pytest.raises(ValueError):
        orch.generate_plan("idea")
    dumps = list(Path("debug/logs").glob("planner_payload_*.json"))
    assert dumps, "payload dump not created"


class _DropResp:
    content = json.dumps({"tasks": [{"id": "T01", "title": "X", "summary": "Y"}]})


def test_normalization_zero(monkeypatch):
    for p in Path("debug/logs").glob("planner_payload_*.json"):
        p.unlink()
    monkeypatch.setattr(orch, "complete", lambda *a, **k: _DropResp())
    monkeypatch.setattr(orch, "select_model", lambda *a, **k: "test")
    monkeypatch.setattr(orch, "normalize_plan_to_tasks", lambda x: x)
    monkeypatch.setattr(orch, "normalize_tasks", lambda x: [])
    with pytest.raises(ValueError) as e:
        orch.generate_plan("idea")
    assert str(e.value) == "planner.normalization_zero"
    dumps = list(Path("debug/logs").glob("planner_payload_*.json"))
    assert dumps, "payload dump not created"
