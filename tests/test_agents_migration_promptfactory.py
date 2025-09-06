import json

from config import feature_flags
from core.agents.base_agent import LLMRoleAgent
from core.agents.marketing_agent import MarketingAgent
from core.agents.planner_agent import PlannerAgent
from core.agents.regulatory_agent import RegulatoryAgent
from core.agents.research_scientist_agent import ResearchScientistAgent
from core.agents.synthesizer_agent import SynthesizerAgent
from dr_rd.prompting.prompt_factory import PromptFactory


def _make_valid():
    return json.dumps({"summary": "", "findings": "", "sources": [{"id": "1", "title": "t"}]})


def _spy_factory(monkeypatch):
    calls = {}
    real = PromptFactory.build_prompt

    def spy(self, spec):
        calls["spec"] = spec
        prompt = real(self, spec)
        calls["prompt"] = prompt
        return prompt

    monkeypatch.setattr(PromptFactory, "build_prompt", spy)
    monkeypatch.setattr(LLMRoleAgent, "act", lambda self, s, u, **k: _make_valid())
    return calls


def test_agents_use_promptfactory(monkeypatch):
    feature_flags.RAG_ENABLED = True
    calls = _spy_factory(monkeypatch)
    ResearchScientistAgent("model").act("idea", "task")
    assert calls["spec"]["io_schema_ref"].endswith("research_v2.json")

    calls = _spy_factory(monkeypatch)
    RegulatoryAgent("model").act("idea", "task")
    assert calls["spec"]["io_schema_ref"].endswith("regulatory_v2.json")

    calls = _spy_factory(monkeypatch)
    MarketingAgent("model").act("idea", "task")
    assert calls["spec"]["io_schema_ref"].endswith("marketing_v2.json")

    calls = _spy_factory(monkeypatch)
    PlannerAgent("model").act("idea", "task")
    assert calls["spec"]["io_schema_ref"].endswith("planner_v1.json")

    calls = _spy_factory(monkeypatch)
    SynthesizerAgent("model").act("idea", {"a": "b"})
    assert calls["spec"]["io_schema_ref"].endswith("synthesizer_v1.json")


def test_retrieval_flag_honored(monkeypatch):
    feature_flags.RAG_ENABLED = False
    calls = _spy_factory(monkeypatch)
    ResearchScientistAgent("model").act("idea", "task")
    assert calls["prompt"]["retrieval"]["enabled"] is False
    feature_flags.RAG_ENABLED = True
    calls = _spy_factory(monkeypatch)
    ResearchScientistAgent("model").act("idea", "task")
    assert calls["prompt"]["retrieval"]["enabled"] is True
