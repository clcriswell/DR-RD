import json

from core.agents.planner_agent import PlannerAgent
from core.agents.research_scientist_agent import ResearchScientistAgent
from core.agents.base_agent import LLMRoleAgent
from config import feature_flags


def test_auto_repair(monkeypatch):
    outputs = ["not json", json.dumps({"summary": "", "findings": "", "sources": []})]
    def fake_act(self, s, u, **k):
        return outputs.pop(0)
    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)
    feature_flags.EVALUATORS_ENABLED = False
    feature_flags.RAG_ENABLED = False
    res = PlannerAgent("model").act("idea", "task")
    assert res
    assert not outputs  # two calls consumed


def test_evaluator_retry(monkeypatch):
    outputs = [
        json.dumps({"summary": "", "findings": "", "sources": []}),
        json.dumps({"summary": "", "findings": "", "sources": [{"id": "1", "title": "t"}]})
    ]
    def fake_act(self, s, u, **k):
        return outputs.pop(0)
    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)
    feature_flags.EVALUATORS_ENABLED = True
    feature_flags.RAG_ENABLED = True
    ResearchScientistAgent("model").act("idea", "task")
    assert not outputs  # evaluator triggered retry
