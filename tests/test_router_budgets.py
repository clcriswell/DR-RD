from core import router
import config.feature_flags as ff


def test_budget_profile_and_simulation_routing(monkeypatch):
    monkeypatch.setattr(ff, "COST_GOVERNANCE_ENABLED", True)
    monkeypatch.setattr(ff, "BUDGET_PROFILE", "low")
    task = {"title": "simulate beam", "description": "", "hints": {}}
    role, cls, model, out = router.route_task(task)
    assert role == "Simulation"
    meta = out["route_decision"]
    assert meta["budget_profile"] == "low"
    assert meta["caps"]["max_tool_calls"] == 1
    assert meta["retrieval_level"] in {"LIGHT", "NONE"}
