import json

from core.orchestrator import _normalize_evidence_payload


def test_payload_normalization_shapes():
    cases = [
        {"claim": 123},
        [{"a": 1}, {"claim": {"x": 2}}],
        [("a", 1), ("claim", 3)],
        [("a", 1, 2), ("claim", 4, 5)],
        "plain text",
        None,
    ]
    outs = [_normalize_evidence_payload(c) for c in cases]
    assert outs[0]["claim"] == "123"
    assert outs[1]["claim"] == json.dumps({"x": 2})
    assert outs[2]["claim"] == "3"
    assert "items" in outs[3]
    assert outs[4]["text"] == "plain text"
    assert outs[5] == {}
