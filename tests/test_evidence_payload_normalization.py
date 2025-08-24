import json

from core.orchestrator import _normalize_evidence_payload


def test_payload_normalization_shapes():
    cases = [
        {"quotes": ["a"], "tokens_in": 1},
        [{"quotes": ["b"]}, {"tokens_out": 2}],
        [("q", "c")],
        ["x", "y"],
        None,
    ]
    outs = [_normalize_evidence_payload(c) for c in cases]
    for out in outs:
        assert isinstance(out.get("quotes"), list)
        json.dumps(out)
