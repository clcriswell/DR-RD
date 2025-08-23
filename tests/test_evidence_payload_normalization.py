import json

from core.orchestrator import _normalize_evidence_payload


def test_payload_normalization_shapes():
    cases = [
        {"claim": 123},
        [{"a": 1}, {"b": 2}],
        [("a", 1), ("b", 2)],
        [("a", 1, 2), ("b", 3, 4)],
        "plain text",
        None,
    ]
    outs = [_normalize_evidence_payload(c) for c in cases]
    for out in outs:
        assert isinstance(out.get("claim"), str)
        json.dumps(out)
