from __future__ import annotations

import json
from pathlib import Path

from dr_rd.billing.quotas import compute_budget


def test_compute_budget(tmp_path: Path) -> None:
    base = tmp_path / "tenants" / "org" / "ws" / "billing"
    base.mkdir(parents=True)
    summary = {"monthly": {"tokens_in": 2_100_000, "tokens_out": 0, "tool_calls": 0, "tool_runtime_ms": 0}}
    (base / "summary_2025-01.json").write_text(json.dumps(summary))
    bw = compute_budget("2025-01", ("org", "ws"), base_dir=tmp_path)
    assert bw.remaining["tokens_in"] == -100000
