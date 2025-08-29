from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import yaml

from .models import BudgetWindow

CFG_PATH = Path("config/billing.yaml")


def _cfg() -> Dict:
    with CFG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def compute_budget(period_ym: str, tenant_key: Tuple[str, str], base_dir: Path | str = Path(".dr_rd")) -> BudgetWindow:
    org, ws = tenant_key
    cfg = _cfg()
    base = Path(base_dir) / "tenants" / org / ws / "billing"
    summary_path = base / f"summary_{period_ym}.json"
    if summary_path.exists():
        usage = json.loads(summary_path.read_text()).get("monthly", {})
    else:
        usage = {}
    soft = cfg.get("quotas", {}).get("soft", {})
    hard = cfg.get("quotas", {}).get("hard", {})
    remaining = {}
    for k in ["tokens_in", "tokens_out", "tool_calls", "tool_runtime_ms"]:
        remaining[k] = hard.get(k, 0) - usage.get(k, 0)
    return BudgetWindow(period=period_ym, soft_quota=soft, hard_quota=hard, usage=usage, remaining=remaining)


__all__ = ["compute_budget"]
