import json

from config import feature_flags
from core.agents.planner_agent import PlannerAgent
from core.agents import prompt_agent


def test_risk_register(monkeypatch):
    def dummy_run(self, spec, **kwargs):
        return json.dumps({"steps": []})

    monkeypatch.setattr(prompt_agent.PromptFactoryAgent, "run_with_spec", dummy_run)
    monkeypatch.setattr(feature_flags, "POLICY_AWARE_PLANNING", True)
    agent = PlannerAgent("dummy")
    res = agent.act("idea", "Call 555-123-4567")
    data = json.loads(res)
    assert "risk_register" in data and data["policy_flags"]["policy_aware"]
    monkeypatch.setattr(feature_flags, "POLICY_AWARE_PLANNING", False)
