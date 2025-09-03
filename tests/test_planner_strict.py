import json
from pathlib import Path

import json
from pathlib import Path

import pytest

import core.orchestrator as orch


class DummyResp:
    content = json.dumps({"tasks": [{"id": "T01", "title": "Do"}]})


def test_planner_strict_validation(monkeypatch):
    monkeypatch.setattr(orch, "complete", lambda *a, **k: DummyResp())
    monkeypatch.setattr(orch, "select_model", lambda *a, **k: "test")
    with pytest.raises(ValueError):
        orch.generate_plan("idea")
    dumps = list(Path("debug/logs").glob("planner_payload_*.json"))
    assert dumps, "payload dump not created"
