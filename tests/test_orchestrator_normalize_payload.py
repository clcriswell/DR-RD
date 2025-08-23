from core.orchestrator import _normalize_evidence_payload


def test_normalize_payload_variants():
    assert _normalize_evidence_payload({"a": 1}) == {"a": 1}

    assert _normalize_evidence_payload([("a", 1), ("b", 2)]) == {"a": 1, "b": 2}

    assert _normalize_evidence_payload([{"a": 1}, {"b": 2}]) == {"a": 1, "b": 2}

    triple = [("a", 1, 2)]
    res = _normalize_evidence_payload(triple)
    assert res["_data"] == triple and "_note" in res

    scalar = 42
    res = _normalize_evidence_payload(scalar)
    assert res["_data"] == scalar
