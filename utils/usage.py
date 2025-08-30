from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Dict

import yaml


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


_PRICING_FILE = Path("config/pricing.yaml")
_DEFAULT_PRICES: Dict[str, Dict[str, float]] = {
    "default": {"input_per_1k": 0.0, "output_per_1k": 0.0}
}


def model_prices() -> Mapping[str, dict]:
    """Return pricing map, loading optional config/pricing.yaml."""
    try:
        data = yaml.safe_load(_PRICING_FILE.read_text(encoding="utf-8"))
        if isinstance(data, Mapping):
            return data  # type: ignore[return-value]
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return _DEFAULT_PRICES


def _price_for(model: str) -> Dict[str, float]:
    prices = model_prices()
    if model in prices:
        return prices[model]
    return prices.get("default", _DEFAULT_PRICES["default"])


def add_delta(
    u: Usage,
    *,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> Usage:
    """Return a new Usage updated with the delta for ``model``."""

    rates = _price_for(model)
    in_rate = float(rates.get("input_per_1k", 0.0))
    out_rate = float(rates.get("output_per_1k", 0.0))
    cost = (prompt_tokens / 1000.0) * in_rate + (completion_tokens / 1000.0) * out_rate
    return Usage(
        prompt_tokens=u.prompt_tokens + prompt_tokens,
        completion_tokens=u.completion_tokens + completion_tokens,
        total_tokens=u.total_tokens + prompt_tokens + completion_tokens,
        cost_usd=round(u.cost_usd + cost, 6),
    )


def merge(a: Usage, b: Usage) -> Usage:
    """Element-wise sum and recompute totals."""
    return Usage(
        prompt_tokens=a.prompt_tokens + b.prompt_tokens,
        completion_tokens=a.completion_tokens + b.completion_tokens,
        total_tokens=a.total_tokens + b.total_tokens,
        cost_usd=round(a.cost_usd + b.cost_usd, 6),
    )


def within_limits(
    u: Usage,
    *,
    budget_limit_usd: Optional[float],
    token_limit: Optional[int],
) -> bool:
    """Return True if ``u`` is within the provided limits."""
    if budget_limit_usd is not None and u.cost_usd > budget_limit_usd:
        return False
    if token_limit is not None and u.total_tokens > token_limit:
        return False
    return True


def thresholds(
    u: Usage,
    *,
    budget_limit_usd: Optional[float],
    token_limit: Optional[int],
) -> dict:
    """Return usage fractions and threshold flags."""
    budget_frac = None
    token_frac = None
    if budget_limit_usd is not None and budget_limit_usd > 0:
        budget_frac = u.cost_usd / budget_limit_usd
    if token_limit is not None and token_limit > 0:
        token_frac = u.total_tokens / token_limit
    budget_crossed = bool(budget_frac is not None and budget_frac >= 0.8)
    token_crossed = bool(token_frac is not None and token_frac >= 0.8)
    budget_exceeded = bool(budget_frac is not None and budget_frac >= 1.0)
    token_exceeded = bool(token_frac is not None and token_frac >= 1.0)
    return {
        "budget_frac": budget_frac,
        "token_frac": token_frac,
        "budget_crossed": budget_crossed,
        "token_crossed": token_crossed,
        "budget_exceeded": budget_exceeded,
        "token_exceeded": token_exceeded,
    }


__all__ = [
    "Usage",
    "model_prices",
    "add_delta",
    "merge",
    "within_limits",
    "thresholds",
]
