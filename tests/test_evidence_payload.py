import json

import pytest

from core.orchestrator import _normalize_evidence_payload


class Dummy:
    def __repr__(self):  # pragma: no cover - trivial
        return "Dummy()"


@pytest.mark.parametrize(
    "payload",
    [
        {"claim": "ok"},
        [{"a": 1}, {"b": 2}],
        [("a", 1), ("b", 2)],
        [("a", 1, 2)],
        Dummy(),
    ],
)
def test_normalizer_claim_string(payload):
    out = _normalize_evidence_payload(payload)
    assert isinstance(out.get("claim"), str)
    json.dumps(out)
