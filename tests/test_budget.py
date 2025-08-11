import pytest
from core.budget import BudgetManager


PRICE_TABLE = {
    "models": {
        "gpt-4o": {"in_per_1k": 0.005, "out_per_1k": 0.015},
        "gpt-3.5-turbo": {"in_per_1k": 0.0005, "out_per_1k": 0.0015},
    }
}
MODE_CFG = {"target_cost_usd": 1.0, "stage_weights": {"plan": 1.0}}


def test_cost_math():
    bm = BudgetManager(MODE_CFG, PRICE_TABLE, safety_margin=0)
    cost = bm.cost_of("gpt-4o", 1000, 1000)
    assert cost == pytest.approx(0.02, rel=1e-6)


def test_cap_behavior():
    bm = BudgetManager(MODE_CFG, PRICE_TABLE, safety_margin=0)
    assert bm.can_afford("plan", "gpt-4o", 100, 100)
    bm.consume(800, 800, "gpt-4o", stage="plan")  # cost 0.016
    assert pytest.approx(bm.spend, rel=1e-6) == 0.016
    # Remaining budget 0.984 -> can afford next small call
    assert bm.can_afford("plan", "gpt-4o", 100, 100)
    # But large call would exceed
    assert not bm.can_afford("plan", "gpt-4o", 50000, 50000)
