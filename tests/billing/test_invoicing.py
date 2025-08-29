from __future__ import annotations

import json
from pathlib import Path

from dr_rd.billing.invoicing import build_invoice


def test_build_invoice(tmp_path: Path) -> None:
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
    inv = build_invoice("2025-01", ("org", "ws"), base_dir=tmp_path)
    assert inv.subtotal_usd > 0
    json_path = base / "invoice_2025-01.json"
    assert json_path.exists()
