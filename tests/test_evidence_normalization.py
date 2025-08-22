from core.observability.evidence import EvidenceItem
from core.orchestrator import _normalize_evidence_payload


def test_dict_claim_and_sources_dict():
    item = EvidenceItem(
        project_id="p",
        role="Marketing Analyst",
        claim={"target_segments": ["fitness centers", "physical therapy clinics"]},
        evidence={"size": 123},
        sources={"urls": ["https://ex.com/a", "https://ex.com/b"]},
        cost_usd="12.5",
    )
    assert isinstance(item.claim, str) and '"target_segments"' in item.claim
    assert isinstance(item.evidence, str) and '"size":123' in item.evidence
    assert item.sources == ["https://ex.com/a", "https://ex.com/b"]
    assert item.cost_usd == 12.5


def test_orchestrator_normalization_meta_and_cost():
    norm = _normalize_evidence_payload({
        "claim": {"x": 1},
        "evidence": ["a", "b"],
        "sources": "https://one.com, https://two.com",
        "cost": "7",
    })
    assert "meta" in norm and "claim_structured" in norm["meta"]
    assert norm["cost_usd"] == "7" or norm["cost_usd"] == 7


def test_sources_mixed_list_and_cost_none():
    item = EvidenceItem(
        project_id="p",
        role="IP Analyst",
        claim="c",
        sources=["https://a.com", {"u": "x"}],
        cost_usd=None,
    )
    assert item.sources[0] == "https://a.com"
    assert item.sources[1].startswith("{")
    assert item.cost_usd == 0.0
