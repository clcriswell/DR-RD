from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _setup_summary(tmp_path: Path) -> Path:
    base = tmp_path / "tenants" / "org" / "ws" / "billing"
    base.mkdir(parents=True)
    summary = {
        "monthly": {
            "tokens_in": 210000,
            "tokens_out": 0,
            "tool_calls": 1001,
            "tool_runtime_ms": 0,
        }
    }
    (base / "summary_2025-01.json").write_text(json.dumps(summary))
    return base


def test_cli_invoice(tmp_path: Path) -> None:
    _setup_summary(tmp_path)
    cmd = ["python", "scripts/billing_cli.py", "invoice", "--month", "2025-01", "--tenant", "org/ws", "--out", str(tmp_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["total_usd"] > 0


def test_generate_invoices_script(tmp_path: Path) -> None:
    _setup_summary(tmp_path)
    cmd = ["python", "scripts/generate_invoices.py", "--month", "2025-01", "--tenant", "org/ws", "--out", str(tmp_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    out = json.loads(res.stdout)
    assert out["total_usd"] > 0
