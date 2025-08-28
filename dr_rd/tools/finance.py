"""Finance analysis helpers."""

from __future__ import annotations

import random
from typing import Dict, List


def calc_unit_economics(line_items: List[Dict]) -> Dict[str, float]:
    """Compute basic unit economics from line items."""
    revenue = sum(i.get("amount", 0) for i in line_items if i.get("type") == "revenue")
    cogs = sum(i.get("amount", 0) for i in line_items if i.get("type") == "cogs")
    other = sum(i.get("amount", 0) for i in line_items if i.get("type") not in {"revenue", "cogs"})
    gross_margin = revenue - cogs
    contribution_margin = gross_margin - other
    return {
        "total_revenue": revenue,
        "total_cost": cogs + other,
        "gross_margin": gross_margin,
        "contribution_margin": contribution_margin,
    }


def npv(cash_flows: List[float], discount_rate: float) -> float:
    """Net present value of cash flows."""
    return sum(cf / (1 + discount_rate) ** i for i, cf in enumerate(cash_flows, start=1))


def monte_carlo(params: Dict[str, Dict[str, float]], trials: int = 2000) -> Dict[str, float]:
    """Monte Carlo simulation over normal distributions."""
    rng = random.Random(0)
    results = []
    for _ in range(trials):
        total = 0.0
        for spec in params.values():
            mu = spec.get("mean", 0.0)
            sigma = spec.get("std", 0.0)
            total += rng.gauss(mu, sigma)
        results.append(total)
    mean_val = sum(results) / trials
    var = sum((x - mean_val) ** 2 for x in results) / trials
    std = var**0.5
    sorted_res = sorted(results)
    p5 = sorted_res[int(0.05 * trials)]
    p95 = sorted_res[int(0.95 * trials)]
    return {"mean": mean_val, "std_dev": std, "p5": p5, "p95": p95}
