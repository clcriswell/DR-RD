from __future__ import annotations

from dr_rd.billing.rates import price_model_call, price_tools


def test_model_pricing() -> None:
    li = price_model_call(1000, 0, provider="openai", model="gpt-4.1-mini")
    assert round(li.amount_usd, 2) == round(0.150 * 1.1, 2)


def test_tool_pricing() -> None:
    li = price_tools(10, 1000)
    assert li.amount_usd == 0.01  # 10 * 0.0005 with markup and rounding
