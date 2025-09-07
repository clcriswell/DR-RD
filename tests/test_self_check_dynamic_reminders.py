import json
from pathlib import Path
import logging

import pytest

from core.evaluation.self_check import validate_and_retry

# Load the real Finance schema to exercise type checks accurately
FINANCE_SCHEMA = json.loads(Path("dr_rd/schemas/finance_v2.json").read_text())


def _valid_finance_json():
    """Return a minimal valid Finance JSON object."""
    return {
        "role": "Finance",
        "task": "t",
        "summary": "s",
        "findings": "f",
        "unit_economics": {
            "total_revenue": 10,
            "total_cost": 5,
            "gross_margin": 5,
            "contribution_margin": 2,
        },
        "npv": 1,
        "simulations": {"mean": 1, "std_dev": 1, "p5": 0, "p95": 2},
        "assumptions": [],
        "risks": ["r"],
        "next_steps": ["n"],
        "sources": [],
    }


# Missing key detection with multiple missing fields

def test_missing_keys_multiple(monkeypatch):
    monkeypatch.setattr(
        "core.evaluation.self_check._load_schema", lambda role: FINANCE_SCHEMA
    )
    bad = _valid_finance_json()
    bad["unit_economics"].pop("total_cost")
    bad["unit_economics"].pop("contribution_margin")
    captured = {}

    def retry_fn(reminder: str) -> str:
        captured["reminder"] = reminder
        fixed = _valid_finance_json()
        return json.dumps(fixed)

    _, meta = validate_and_retry(
        "Finance", {"title": "t"}, json.dumps(bad), retry_fn
    )
    assert "missing 'total_cost'" in captured["reminder"]
    assert "missing 'contribution_margin'" in captured["reminder"]
    assert meta == {"retried": True, "valid_json": True, "missing_keys": []}


# Type mismatch errors and corresponding hints

def test_type_mismatch_numeric(monkeypatch):
    monkeypatch.setattr(
        "core.evaluation.self_check._load_schema", lambda role: FINANCE_SCHEMA
    )
    bad = _valid_finance_json()
    bad["npv"] = "Not determined"
    captured = {}

    def retry_fn(reminder: str) -> str:
        captured["reminder"] = reminder
        return json.dumps(bad)

    validate_and_retry("Finance", {"title": "t"}, json.dumps(bad), retry_fn)
    assert "numeric field" in captured["reminder"]


def test_type_mismatch_array(monkeypatch):
    monkeypatch.setattr(
        "core.evaluation.self_check._load_schema", lambda role: FINANCE_SCHEMA
    )
    bad = _valid_finance_json()
    bad["risks"] = "All good"
    captured = {}

    def retry_fn(reminder: str) -> str:
        captured["reminder"] = reminder
        return json.dumps(bad)

    validate_and_retry("Finance", {"title": "t"}, json.dumps(bad), retry_fn)
    assert "array was required" in captured["reminder"]


# Combined errors (missing key + type mismatch)

def test_combined_errors(monkeypatch):
    monkeypatch.setattr(
        "core.evaluation.self_check._load_schema", lambda role: FINANCE_SCHEMA
    )
    bad = _valid_finance_json()
    bad["unit_economics"].pop("total_cost")
    bad["findings"] = ["list"]  # should be a single string
    captured = {}

    def retry_fn(reminder: str) -> str:
        captured["reminder"] = reminder
        fixed = _valid_finance_json()
        return json.dumps(fixed)

    _, meta = validate_and_retry(
        "Finance", {"title": "t"}, json.dumps(bad), retry_fn
    )
    assert "missing 'total_cost'" in captured["reminder"]
    assert "used a list where a single string was required" in captured["reminder"]
    assert " and " in captured["reminder"]
    assert meta == {"retried": True, "valid_json": True, "missing_keys": []}


# Logging/trace output for retry attempts

def test_retry_logging(monkeypatch, caplog):
    from core.evaluation import self_check

    events = []

    def fake_append_step(run_id, payload):
        events.append(payload)

    monkeypatch.setattr(self_check, "_load_schema", lambda role: None)
    monkeypatch.setattr(self_check.trace_writer, "append_step", fake_append_step)

    caplog.set_level(logging.INFO)

    def retry_fn(reminder: str) -> str:
        return "still bad"

    validate_and_retry(
        "Finance", {"title": "t", "id": "task"}, "not json", retry_fn, run_id="run"
    )

    assert any(e["event"] == "retry_prompt" for e in events)
    assert any(e["event"] == "validation_error" for e in events)
    record = next(r for r in caplog.records if r.message == "retry_prompt")
    assert record.role == "Finance"
    assert "Reminder:" in record.prompt


# Successful retries using a second corrected JSON

def test_retry_success_after_type_fix(monkeypatch):
    monkeypatch.setattr(
        "core.evaluation.self_check._load_schema", lambda role: FINANCE_SCHEMA
    )
    bad = _valid_finance_json()
    bad["npv"] = "Not determined"
    captured = {}

    def retry_fn(reminder: str) -> str:
        captured["reminder"] = reminder
        fixed = _valid_finance_json()
        return json.dumps(fixed)

    _, meta = validate_and_retry(
        "Finance", {"title": "t"}, json.dumps(bad), retry_fn
    )
    assert meta == {"retried": True, "valid_json": True, "missing_keys": []}
    assert "numeric field" in captured["reminder"]
