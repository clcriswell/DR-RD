from __future__ import annotations

import json
from pathlib import Path

import pytest

from utils import health_check as hc


def _patch_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path / ".dr_rd"
    monkeypatch.setattr(hc, "DR_DIR", base)
    monkeypatch.setattr(hc, "TELEMETRY_DIR", base / "telemetry")
    monkeypatch.setattr(hc, "RUNS_DIR", base / "runs")


def test_run_all_basic(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)
    monkeypatch.setenv("NO_NET", "1")
    report = hc.run_all()
    assert isinstance(report.summary, dict)
    assert report.checks
    assert report.env["python"]
    data = json.loads(hc.to_json(report).decode("utf-8"))
    assert data["summary"] == report.summary
    md = hc.to_markdown(report)
    assert "| id | status | name | remedy |" in md


def test_filesystem_probe_fail(monkeypatch):
    ro = Path("/proc/ro")
    monkeypatch.setattr(hc, "DR_DIR", ro)
    monkeypatch.setattr(hc, "TELEMETRY_DIR", ro / "telemetry")
    monkeypatch.setattr(hc, "RUNS_DIR", ro / "runs")
    monkeypatch.setenv("NO_NET", "1")
    report = hc.run_all()
    fs = [c for c in report.checks if c.id == "filesystem"][0]
    assert fs.status == "fail"
