import os

import pytest

from core.agents import registry


class NoCall:
    def __init__(self, *args, **kwargs):
        pass


class DummySynth:
    def __init__(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        return "ok"


def _patched_agents():
    return {"Synthesizer": DummySynth, "Dummy": NoCall}


def test_validation_skipped(monkeypatch):
    monkeypatch.setattr(registry, "AGENTS", _patched_agents())
    registry.CACHE.clear()
    res = registry.validate_registry(strict=False)
    assert res["errors"][0][0] == "Dummy"


def test_validation_strict(monkeypatch):
    monkeypatch.setattr(registry, "AGENTS", _patched_agents())
    registry.CACHE.clear()
    monkeypatch.setenv("DRRD_STRICT_AGENT_REGISTRY", "true")
    with pytest.raises(RuntimeError):
        registry.validate_registry()
