import json
from pathlib import Path

import pytest

from utils import prefs


def _patch_config(tmp_path: Path, monkeypatch):
    cfg_dir = tmp_path / ".dr_rd"
    monkeypatch.setattr(prefs, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(prefs, "CONFIG_PATH", cfg_dir / "config.json")


def test_load_creates_defaults(tmp_path, monkeypatch):
    _patch_config(tmp_path, monkeypatch)
    if prefs.CONFIG_PATH.exists():
        prefs.CONFIG_PATH.unlink()
    loaded = prefs.load_prefs()
    assert loaded == prefs.DEFAULT_PREFS
    assert prefs.CONFIG_PATH.exists()


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    _patch_config(tmp_path, monkeypatch)
    data = prefs.DEFAULT_PREFS.copy()
    data["defaults"] = data["defaults"].copy()
    data["defaults"]["mode"] = "deep"
    prefs.save_prefs(data)
    loaded = prefs.load_prefs()
    assert loaded["defaults"]["mode"] == "deep"
    assert loaded["version"] == prefs.DEFAULT_PREFS["version"]


def test_invalid_values_coerced(tmp_path, monkeypatch):
    _patch_config(tmp_path, monkeypatch)
    bad = {
        "version": 1,
        "defaults": {"max_tokens": "1000", "extra": True},
        "ui": {"trace_page_size": 500},
        "privacy": {"telemetry_enabled": "yes", "unknown": True},
        "other": {"x": 1},
    }
    prefs.save_prefs(bad)
    loaded = prefs.load_prefs()
    assert loaded["defaults"]["max_tokens"] == 1000
    assert "extra" not in loaded["defaults"]
    assert loaded["ui"]["trace_page_size"] == 200
    assert loaded["privacy"]["telemetry_enabled"] is True
    assert "unknown" not in loaded["privacy"]
    assert "other" not in loaded


def test_merge_defaults(tmp_path, monkeypatch):
    _patch_config(tmp_path, monkeypatch)
    data = prefs.DEFAULT_PREFS.copy()
    data["defaults"] = data["defaults"].copy()
    data["defaults"]["mode"] = "test"
    prefs.save_prefs(data)
    base = {"mode": "standard", "max_tokens": 8000, "budget_limit_usd": None, "knowledge_sources": []}
    merged = prefs.merge_defaults(base)
    assert merged["mode"] == "test"
    assert merged["max_tokens"] == 8000
    assert "budget_limit_usd" in merged


def test_trace_page_size_clamped(tmp_path, monkeypatch):
    _patch_config(tmp_path, monkeypatch)
    data = prefs.DEFAULT_PREFS.copy()
    data["ui"] = data["ui"].copy()
    data["ui"]["trace_page_size"] = 5
    prefs.save_prefs(data)
    loaded = prefs.load_prefs()
    assert loaded["ui"]["trace_page_size"] == 10
