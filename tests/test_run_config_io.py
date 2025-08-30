import pytest

from utils import run_config_io


def test_round_trip_and_truncation():
    cfg = {
        "idea": "x" * 300,
        "mode": "standard",
        "budget_limit_usd": 5.0,
        "max_tokens": 1000,
        "knowledge_sources": ["a", "b"],
        "advanced": {"foo": "bar"},
        "seed": 42,
        "extra": "drop",
    }
    lock = run_config_io.to_lockfile(cfg)
    assert lock["inputs"]["idea"] == "x" * 200
    out = run_config_io.from_lockfile(lock)
    assert out == {
        "idea": "x" * 200,
        "mode": "standard",
        "budget_limit_usd": 5.0,
        "max_tokens": 1000,
        "knowledge_sources": ["a", "b"],
        "advanced": {"foo": "bar"},
        "seed": 42,
    }


def test_type_validation():
    bad = {
        "schema": run_config_io.SCHEMA_VERSION,
        "created_at": 0,
        "inputs": {"idea": "ok", "knowledge_sources": "oops"},
    }
    with pytest.raises(ValueError):
        run_config_io.from_lockfile(bad)
