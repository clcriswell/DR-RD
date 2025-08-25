#!/usr/bin/env python3
"""Analyze run logs or fall back to static repo analysis."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = ROOT / "docs" / "UNIFIED_MODE_REPORT.md"


def _read_logs(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if path.is_dir():
        files = sorted(path.glob("*.csv"))
    else:
        files = [path]
    for fp in files:
        try:
            with fp.open() as fh:
                reader = csv.DictReader(fh)
                rows.extend(list(reader))
        except FileNotFoundError:
            continue
    return rows


def _summarize_rows(rows: List[Dict[str, str]]) -> Dict[str, int]:
    stats = {
        "planner": 0,
        "router": 0,
        "executor": 0,
        "synthesizer": 0,
        "registry_lookups": 0,
        "json_errors": 0,
        "evaluators": 0,
        "retrieval_calls": 0,
        "web_calls": 0,
    }
    for row in rows:
        blob = " ".join(row.values()).lower()
        if "planner" in blob:
            stats["planner"] += 1
        if "router" in blob or "registry" in blob:
            stats["router"] += 1
            if "registry" in blob:
                stats["registry_lookups"] += 1
        if "executor" in blob:
            stats["executor"] += 1
        if "synth" in blob:
            stats["synthesizer"] += 1
        if "json" in blob and ("error" in blob or "retry" in blob):
            stats["json_errors"] += 1
        if "evaluator" in blob:
            stats["evaluators"] += 1
        if "rag" in blob or "retrieval" in blob:
            stats["retrieval_calls"] += 1
        if "web" in blob and "search" in blob:
            stats["web_calls"] += 1
    return stats


def _static_deprecations() -> List[Dict[str, str]]:
    return [
        {
            "path": "orchestrators/router.py",
            "role": "router shim",
            "used_by": "",
            "mode_conditional": "no",  # noqa: E501
            "duplicate_of": "core/router.py",
            "canonical_target": "core.router",
            "action": "safe_delete",
            "rationale": "re-export removed",
        },
        {
            "path": "core/agents_registry.py",
            "role": "agent registry shim",
            "used_by": "",
            "mode_conditional": "no",  # noqa: E501
            "duplicate_of": "core/agents/unified_registry.py",
            "canonical_target": "core.agents.unified_registry",
            "action": "safe_delete",
            "rationale": "unified registry",
        },
        {
            "path": "config/mode_profiles.py",
            "role": "profile shim",
            "used_by": "",
            "mode_conditional": "yes",  # noqa: E501
            "duplicate_of": "config/modes.yaml",
            "canonical_target": "standard profile",
            "action": "safe_delete",
            "rationale": "single profile",
        },
        {
            "path": "evaluators/*",
            "role": "evaluator package",
            "used_by": "",
            "mode_conditional": "no",  # noqa: E501
            "duplicate_of": "dr_rd/evaluators/*",
            "canonical_target": "dr_rd.evaluators",
            "action": "migrate_copy",
            "rationale": "package relocated",
        },
    ]


def build_report(rows: List[Dict[str, str]]) -> str:
    stats = _summarize_rows(rows) if rows else None
    dep = _static_deprecations()
    lines = ["# Unified Mode Report", ""]
    if stats:
        lines.append("## Findings")
        lines.append(json.dumps(stats, indent=2))
        lines.append("")
    else:
        lines.append("## Findings")
        lines.append("No logs found; using static analysis only.")
        lines.append("")
    lines.append("## Deprecation Classification")
    lines.append(
        "| path | role | used_by | mode-conditional? | duplicate_of | canonical_target | action | rationale |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for d in dep:
        lines.append(
            f"| {d['path']} | {d['role']} | {d['used_by']} | {d['mode_conditional']} | "  # noqa: E501
            f"{d['duplicate_of']} | {d['canonical_target']} | {d['action']} | {d['rationale']} |"  # noqa: E501
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", type=str, default="logs", help="CSV log file or directory")
    args = ap.parse_args()
    path = Path(args.path)
    rows = _read_logs(path) if path.exists() else []
    report = build_report(rows)
    DOC_PATH.write_text(report)
    print(f"Wrote {DOC_PATH}")


if __name__ == "__main__":
    main()
