import json

import pytest

from core.orchestrator import _normalize_evidence_payload


class Dummy:
    def __repr__(self):  # pragma: no cover - trivial
        return "Dummy()"


@pytest.mark.parametrize(
    "payload",
    [
        {"quotes": ["ok"]},
        [{"quotes": ["a"]}, {"tokens_in": 2}],
        [("q1", "c1")],
        ["a", "b"],
        Dummy(),
    ],
)
def test_normalizer_returns_serializable(payload):
    out = _normalize_evidence_payload(payload)
    assert isinstance(out.get("quotes"), list)
    json.dumps(out)
