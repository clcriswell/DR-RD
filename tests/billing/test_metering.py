from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from dr_rd.billing.metering import aggregate_month, collect_usage


def test_collect_and_aggregate(tmp_path: Path) -> None:
    log = tmp_path / "telemetry.jsonl"
    events = [
        {
            "ts": "2025-01-01T00:00:00",
            "org_id": "org",
            "workspace_id": "ws",
            "run_id": "r1",
            "phase": "plan",
            "tokens_in": 10,
            "tokens_out": 20,
            "tool_calls": 1,
            "tool_runtime_ms": 100,
        },
        {
            "ts": "2025-01-02T00:00:00",
            "org_id": "org",
            "workspace_id": "ws",
            "run_id": "r2",
            "phase": "exec",
            "tokens_in": 30,
            "tokens_out": 40,
            "tool_calls": 2,
            "tool_runtime_ms": 200,
        },
    ]
    with log.open("w", encoding="utf-8") as fh:
        for e in events:
            fh.write(json.dumps(e) + "\n")
    usage_events = collect_usage([log])
    assert len(usage_events) == 2
    agg = aggregate_month(usage_events)
    assert agg[("org", "ws")]["monthly"]["tokens_in"] == 40
    assert agg[("org", "ws")]["monthly"]["tool_calls"] == 3
