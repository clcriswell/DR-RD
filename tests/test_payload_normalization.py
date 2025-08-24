from core.orchestrator import _normalize_evidence_payload


def test_normalize_dict():
    p = {"quotes": ["a"], "tokens_in": 10, "tokens_out": 5, "citations": ["u"], "cost": 0.1}
    out = _normalize_evidence_payload(p)
    assert out["quotes"] == ["a"]
    assert out["tokens_in"] == 10
    assert out["tokens_out"] == 5
    assert out["citations"] == ["u"]
    assert out["cost"] == 0.1


def test_normalize_list_of_strings():
    p = ["q1", "q2"]
    out = _normalize_evidence_payload(p)
    assert out["quotes"] == ["q1", "q2"]


def test_normalize_list_of_dicts():
    p = [{"quotes": ["a"], "tokens_in": 2, "cost": 0.2}, {"quotes": ["b"], "tokens_out": 3, "citations": ["c"]}]
    out = _normalize_evidence_payload(p)
    assert out["quotes"] == ["a", "b"]
    assert out["tokens_in"] == 2
    assert out["tokens_out"] == 3
    assert out["citations"] == ["c"]
    assert out["cost"] == 0.2
