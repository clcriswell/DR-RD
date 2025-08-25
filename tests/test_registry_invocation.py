import logging
import pytest

import core.router as router
import core.agents.unified_registry as registry
from core.agents.invoke import resolve_invoker


class DummyRun:
    def __init__(self, model=None):
        self.model = model

    def run(self, *, task, model=None, meta=None):
        return {"ok": True}


class DummyInvoke:
    def __init__(self, model=None):
        self.model = model

    def invoke(self, *, task=None, model=None, meta=None):
        return {"method": "invoke"}


class DummyCall:
    def __init__(self, model=None):
        self.model = model

    def __call__(self, *, task=None, model=None, meta=None):
        return {"method": "call"}


class DummyNoCallable:
    def __init__(self, model=None):
        self.model = model


class DummySynth:
    def __init__(self, model=None):
        self.model = model

    def run(self, *, task, model=None, meta=None):
        return {"synth": True}


def test_resolve_invoker_precedence():
    attr, _ = resolve_invoker(DummyRun())
    assert attr == "run"
    attr, _ = resolve_invoker(DummyInvoke())
    assert attr == "invoke"
    attr, _ = resolve_invoker(DummyCall())
    assert attr == "__call__"


def test_validate_registry_reports_errors_and_strict(monkeypatch):
    monkeypatch.setattr(
        registry, "AGENT_REGISTRY", {"OK": DummyRun, "Bad": DummyNoCallable}
    )
    monkeypatch.setattr(registry, "AGENTS", registry.AGENT_REGISTRY)
    monkeypatch.setattr(registry, "select_model", lambda *a, **k: "m")
    registry.CACHE.clear()
    summary = registry.validate_registry(strict=False)
    assert summary["ok"] == ["OK"]
    assert summary["errors"][0][0] == "Bad"
    monkeypatch.setenv("DRRD_STRICT_AGENT_REGISTRY", "true")
    registry.CACHE.clear()
    with pytest.raises(RuntimeError):
        registry.validate_registry()
    monkeypatch.delenv("DRRD_STRICT_AGENT_REGISTRY", raising=False)


def test_router_fallback_to_synthesizer(monkeypatch, caplog):
    def fake_get_agent(name):
        return DummyNoCallable() if name == "Regulatory" else DummySynth()

    monkeypatch.setattr(router, "get_agent", fake_get_agent)
    monkeypatch.setattr(router, "select_model", lambda *a, **k: "m")
    with caplog.at_level(logging.WARNING):
        result = router.dispatch({"role": "Regulatory", "title": "", "description": ""})
    assert result == {"synth": True}
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "Regulatory" in warnings[0].message


def test_dispatch_success(monkeypatch):
    monkeypatch.setattr(router, "get_agent", lambda name: DummyRun())
    monkeypatch.setattr(router, "select_model", lambda *a, **k: "m")
    result = router.dispatch({"role": "Planner", "title": "", "description": ""})
    assert result == {"ok": True}

