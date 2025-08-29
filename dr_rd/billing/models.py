from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class UsageEvent:
    ts: datetime
    org_id: str
    workspace_id: str
    run_id: str
    phase: str
    agent: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    tokens_in: int = 0
    tokens_out: int = 0
    tool_calls: int = 0
    tool_runtime_ms: int = 0
    retrieval_docs: int = 0
    cache_bytes: int = 0
    meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class CostLineItem:
    kind: str  # 'model' or 'tools'
    org_id: str
    workspace_id: str
    period: str  # YYYY-MM
    quantity: float
    unit: str
    unit_price_usd: float
    amount_usd: float
    meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class BudgetWindow:
    period: str  # YYYY-MM
    soft_quota: Dict[str, int]
    hard_quota: Dict[str, int]
    usage: Dict[str, int]
    remaining: Dict[str, int]


@dataclass
class Invoice:
    invoice_id: str
    org_id: str
    workspace_id: str
    period: str
    line_items: List[CostLineItem]
    subtotal_usd: float
    tax_usd: float
    total_usd: float
    usage_summary: Dict[str, int]
    notes: str = ""


__all__ = [
    "UsageEvent",
    "CostLineItem",
    "BudgetWindow",
    "Invoice",
]
