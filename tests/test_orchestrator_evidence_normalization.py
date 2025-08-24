import json

import pytest

from core.orchestrator import _normalize_evidence_payload


@pytest.mark.parametrize(
    "payload",
    [
        {"quotes": ["c"], "citations": ["s1"], "cost": "1.2"},
        '{"quotes": ["c"], "citations": ["s1"]}',
        [("q1", "c")],
        [{"quotes": ["c"]}, {"tokens_in": 1}],
        ["a", "b"],
        None,
    ],
)
def test_normalization_returns_dict(payload):
    out = _normalize_evidence_payload(payload)
    assert isinstance(out, dict)
    assert isinstance(out.get("quotes"), list)
