import json

from core.agents.ip_analyst_agent import IPAnalystAgent
from core.agents.prompt_agent import PromptFactoryAgent
from core.agents.regulatory_agent import RegulatoryAgent
from dr_rd.evaluators import patent_overlap_check, reg_citation_check


def test_regulatory_agent_policy(monkeypatch):
    agent = RegulatoryAgent("gpt-4o-mini")
    captured = {}
    monkeypatch.setattr(
        PromptFactoryAgent,
        "run_with_spec",
        lambda self, spec, **k: captured.setdefault("spec", spec) or "{}",
    )
    agent.act("idea", {"description": "ensure CFR compliance"})
    spec = captured["spec"]
    assert spec["io_schema_ref"].endswith("regulatory_evidence_v1.json")
    assert spec["retrieval_policy"].name == "AGGRESSIVE"


def test_ip_agent_schema(monkeypatch):
    agent = IPAnalystAgent("gpt-4o-mini")
    captured = {}
    monkeypatch.setattr(
        PromptFactoryAgent,
        "run_with_spec",
        lambda self, spec, **k: captured.setdefault("spec", spec) or "{}",
    )
    agent.act("idea", {"description": "find prior art"})
    spec = captured["spec"]
    assert spec["io_schema_ref"].endswith("patent_evidence_v1.json")
    assert spec["retrieval_policy"].name == "AGGRESSIVE"
    assert isinstance(spec.get("top_k"), int)


def test_evaluators():
    bad = {"records": [{"agency": "EPA", "cfr_refs": [], "source": {"id": "1", "url": "u"}}]}
    ok, _ = reg_citation_check(bad)
    assert not ok
    good = {
        "records": [{"agency": "EPA", "cfr_refs": ["40 CFR"], "source": {"id": "1", "url": "u"}}]
    }
    ok2, _ = reg_citation_check(good)
    assert ok2
    patent_bad = {
        "records": [
            {
                "pub_number": "US1",
                "cpc_codes": [],
                "ipc_codes": [],
                "source": {"id": "1", "url": "u"},
            }
        ]
    }
    ok3, _ = patent_overlap_check(patent_bad)
    assert not ok3
