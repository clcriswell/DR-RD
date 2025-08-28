"""Simple diff diagnostics evaluation."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml  # type: ignore


@dataclass
class Finding:
    id: str
    severity: str
    msg: str
    evidence: Dict[str, Any]


def load_rules(path: str | Path = "config/diagnostics.yaml") -> Dict[str, Any]:
    return yaml.safe_load(Path(path).read_text())


def evaluate_diff(diff: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[Finding] = []
    sev = "info"

    # Latency
    latency = abs(diff.get("latency_delta_ms_total", 0))
    lat_cfg = rules.get("latency", {})
    if latency > lat_cfg.get("fail_ms", float("inf")):
        sev = "fail"
        findings.append(Finding("latency", "fail", "latency regression", {"delta": latency}))
    elif latency > lat_cfg.get("warn_ms", float("inf")):
        sev = "warn"
        findings.append(Finding("latency", "warn", "latency regression", {"delta": latency}))

    # Failure rate
    fr = diff.get("tool_failure_rate", {}).get("delta", 0.0)
    fr_cfg = rules.get("failure_rate", {})
    if fr > fr_cfg.get("fail_delta", float("inf")):
        sev = max(sev, "fail", key=["info", "warn", "fail"].index)  # type: ignore
        findings.append(Finding("failure_rate", "fail", "failure rate increased", {"delta": fr}))
    elif fr > fr_cfg.get("warn_delta", float("inf")) and sev != "fail":
        sev = "warn"
        findings.append(Finding("failure_rate", "warn", "failure rate increased", {"delta": fr}))

    return {
        "severity": sev,
        "findings": [f.__dict__ for f in findings],
    }


__all__ = ["load_rules", "evaluate_diff"]
