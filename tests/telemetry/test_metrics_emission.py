import json
import importlib
from pathlib import Path


def test_metrics_emission(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("TELEMETRY_LOG_DIR", str(log_dir))
    monkeypatch.setenv("TELEMETRY_ENABLED", "true")
    monkeypatch.setenv("TELEMETRY_SAMPLING_RATE", "1.0")
    m = importlib.reload(importlib.import_module("dr_rd.telemetry.metrics"))
    m.inc("runs_started", agent="tester")
    m.observe("run_duration_ms", 123, agent="tester")
    files = list(log_dir.glob("*.jsonl"))
    assert files, "metric file not written"
    lines = [json.loads(line) for line in files[0].read_text().splitlines()]
    assert any(e["name"] == "runs_started" for e in lines)
    assert any(e["name"] == "run_duration_ms" for e in lines)


def test_sampling_respected(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("TELEMETRY_LOG_DIR", str(log_dir))
    monkeypatch.setenv("TELEMETRY_ENABLED", "true")
    monkeypatch.setenv("TELEMETRY_SAMPLING_RATE", "0.0")
    m = importlib.reload(importlib.import_module("dr_rd.telemetry.metrics"))
    m.inc("runs_started")
    assert not list(log_dir.glob("*.jsonl"))
