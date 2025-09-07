from __future__ import annotations

import json
from pathlib import Path
from contextlib import contextmanager
from typing import List

from core import ui_bridge


def test_run_specialist_passes_flags(monkeypatch):
    called = {}

    def fake_get(role):
        called["role"] = role
        return object()

    @contextmanager
    def fake_flags(overrides):
        called["overrides"] = overrides
        yield

    def fake_exec(role, title, desc, inputs, flag_overrides, agent=None):
        called["exec_overrides"] = flag_overrides
        return {"role": role, "output": {}}

    monkeypatch.setattr(ui_bridge, "_apply_flag_overrides", fake_flags)
    monkeypatch.setattr("core.agents.unified_registry.get_agent", fake_get)
    monkeypatch.setattr("core.runner.execute_task", fake_exec)

    res = ui_bridge.run_specialist("Materials Engineer", "t", "d", {}, {"RAG_ENABLED": False})
    assert res["role"] == "Materials Engineer"
    assert called["exec_overrides"] == {"RAG_ENABLED": False}
    assert called["role"] == "Materials Engineer"


def test_run_dynamic_passes_flags(monkeypatch):
    called = {}

    class FakeAgent:
        def __init__(self, model):
            called["model"] = model

        def run(self, spec):
            called["spec"] = spec
            return {"out": 1}, {}

    @contextmanager
    def fake_flags(overrides):
        called["overrides"] = overrides
        yield

    monkeypatch.setattr(ui_bridge, "_apply_flag_overrides", fake_flags)
    monkeypatch.setattr(ui_bridge, "DynamicAgent", FakeAgent)
    monkeypatch.setattr("core.llm.select_model", lambda *a, **k: "m")

    res = ui_bridge.run_dynamic({"x": 1}, {"RAG_ENABLED": True})
    assert res == {"out": 1}
    assert called["overrides"] == {"RAG_ENABLED": True}
    assert called["spec"] == {"x": 1}


def test_load_provenance(tmp_path: Path):
    log = tmp_path / "run1" / "provenance.jsonl"
    log.parent.mkdir()
    lines: List[str] = ['{"ts":1}', '{"ts":2}']
    log.write_text("\n".join(lines), encoding="utf-8")
    out = ui_bridge.load_provenance(str(tmp_path), limit=1)
    assert len(out) == 1 and out[0]["ts"] == 2
