from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict

import yaml

from .models import CostLineItem

CFG_PATH = Path("config/billing.yaml")
MODELS_CFG = Path("config/models.yaml")
TOOLS_CFG = Path("config/tools.yaml")


def _config() -> Dict:
    with CFG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _round(amount: float, cents: int) -> float:
    q = Decimal(amount).quantize(Decimal(10) ** -cents, ROUND_HALF_UP)
    return float(q)


def _model_prices(provider: str, model: str) -> tuple[float, float]:
    with MODELS_CFG.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    prov = cfg.get("providers", {}).get(provider, {})
    for m in prov.get("models", []):
        if m.get("name") == model:
            return float(m.get("price_per_1k_in", 0)), float(m.get("price_per_1k_out", 0))
    return 0.0, 0.0


def price_model_call(tokens_in: int, tokens_out: int, provider: str, model: str) -> CostLineItem:
    cfg = _config()
    billing = cfg.get("billing", {})
    p_in, p_out = _model_prices(provider, model)
    amount = (tokens_in / 1000) * p_in + (tokens_out / 1000) * p_out
    markup = billing.get("markups", {}).get("model", 0)
    amount *= (1 + markup)
    amount = _round(amount, billing.get("rounding", {}).get("cents", 2))
    unit_price = amount / max(tokens_in + tokens_out, 1)
    return CostLineItem(
        kind="model",
        org_id="",
        workspace_id="",
        period="",
        quantity=tokens_in + tokens_out,
        unit="token",
        unit_price_usd=_round(unit_price, billing.get("rounding", {}).get("cents", 2)),
        amount_usd=amount,
    )


def price_tools(tool_calls: int, tool_runtime_ms: int, breakdown: Dict | None = None) -> CostLineItem:
    cfg = _config()
    billing = cfg.get("billing", {})
    default_cost = cfg.get("rates", {}).get("tools_default_cost_per_call_usd", 0.0)
    amount = tool_calls * default_cost
    markup = billing.get("markups", {}).get("tools", 0)
    amount *= (1 + markup)
    amount = _round(amount, billing.get("rounding", {}).get("cents", 2))
    unit_price = amount / max(tool_calls, 1)
    return CostLineItem(
        kind="tools",
        org_id="",
        workspace_id="",
        period="",
        quantity=tool_calls,
        unit="call",
        unit_price_usd=_round(unit_price, billing.get("rounding", {}).get("cents", 2)),
        amount_usd=amount,
        meta={"runtime_ms": tool_runtime_ms, "breakdown": breakdown or {}},
    )


__all__ = ["price_model_call", "price_tools"]
