from core.orchestrator import _normalize_evidence_payload


def test_dict_passthrough():
    payload = {"claim": "c", "evidence": "e"}
    assert _normalize_evidence_payload(payload) == payload


def test_list_of_dicts_merge():
    payload = [{"claim": "c"}, {"evidence": "e"}]
    assert _normalize_evidence_payload(payload) == {"claim": "c", "evidence": "e"}


def test_pair_sequence():
    payload = [("claim", "c"), ("evidence", "e")]
    assert _normalize_evidence_payload(payload) == {"claim": "c", "evidence": "e"}


def test_irregular_shapes():
    payload = [("a", 1, 2)]
    out = _normalize_evidence_payload(payload)
    assert "data" in out


def test_scalar_value():
    payload = "hello"
    assert _normalize_evidence_payload(payload) == {"value": "hello"}
