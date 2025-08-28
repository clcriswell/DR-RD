import json

from core.agents.research_scientist_agent import ResearchScientistAgent
from core.agents.base_agent import LLMRoleAgent
from config import feature_flags


def test_rag_on_includes_citations(monkeypatch):
    captured = {}
    def fake_act(self, sys, user, **k):
        captured["system"] = sys
        return json.dumps({"summary": "", "findings": "", "sources": [{"id": "1", "title": "t"}]})
    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)
    feature_flags.RAG_ENABLED = True
    out = ResearchScientistAgent("model").act("idea", "task")
    assert "Retrieval policy" in captured["system"]
    assert json.loads(out)["sources"]


def test_rag_off_no_citation_language(monkeypatch):
    captured = {}
    def fake_act(self, sys, user, **k):
        captured["system"] = sys
        return json.dumps({"summary": "", "findings": "", "sources": []})
    monkeypatch.setattr(LLMRoleAgent, "act", fake_act)
    feature_flags.RAG_ENABLED = False
    out = ResearchScientistAgent("model").act("idea", "task")
    assert "Retrieval policy" not in captured["system"]
    assert not json.loads(out)["sources"]
