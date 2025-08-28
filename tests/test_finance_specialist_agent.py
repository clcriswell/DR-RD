import json

from core.agents.finance_specialist_agent import FinanceSpecialistAgent
from core.llm import ChatResult


def test_finance_agent(monkeypatch):
    output = {
        "role": "Finance Specialist",
        "task": "eval",
        "unit_economics": {
            "total_revenue": 100,
            "total_cost": 60,
            "gross_margin": 40,
            "contribution_margin": 20,
        },
        "npv": 10.0,
        "simulations": {"mean": 1.0, "std_dev": 0.1, "p5": 0.8, "p95": 1.2},
        "assumptions": [],
        "risks": [],
        "next_steps": [],
        "sources": [],
    }

    def fake_complete(system, user, model=None, **kwargs):
        return ChatResult(content=json.dumps(output), raw={})

    monkeypatch.setattr("core.agents.finance_specialist_agent.complete", fake_complete)
    agent = FinanceSpecialistAgent("gpt")
    items = [{"type": "revenue", "amount": 100}, {"type": "cogs", "amount": 60}]
    res = agent.run("eval", items, [10.0], {"x": {"mean": 1.0, "std": 0.1}})
    assert res["unit_economics"]["gross_margin"] == 40
    assert res["npv"] == 10.0
