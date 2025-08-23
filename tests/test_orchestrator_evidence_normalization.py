import json

import pytest

from core.orchestrator import _normalize_evidence_payload


@pytest.mark.parametrize(
    "payload",
    [
        {"claim": "c", "sources": ["s1"], "cost": "1.2"},
        '{"claim": "c", "sources": ["s1"]}',
        [("claim", "c"), ("sources", ["s1"])],
        [("claim", "c", 1), ("sources", ["s1"], 2)],
        [{"claim": "c"}, {"sources": ["s1"]}],
        ["a", "b"],
        None,
    ],
)
def test_normalization_returns_dict_and_claim_str(payload):
    out = _normalize_evidence_payload(payload)
    assert isinstance(out, dict)
    assert isinstance(out.get("claim", ""), str)
