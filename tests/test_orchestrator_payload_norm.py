from types import SimpleNamespace
import pytest

import core.orchestrator as orch


def test_normalize_payload_list_quotes_tokens(monkeypatch):
    monkeypatch.setattr(
        orch,
        "extract_json_block",
        lambda txt: [
            {"quotes": [{"q": "x"}]},
            {"tokens_in": 7},
            {"tokens_out": 11},
        ],
    )
    added = {}

    class DummyEvidence:
        def add(self, **kw):
            added.update(kw)

    monkeypatch.setattr(orch, "evidence", DummyEvidence())

    def _normalize_evidence_payload(payload):
        if isinstance(payload, list):
            res = {}
            for item in payload:
                if isinstance(item, dict):
                    res.update(item)
            return res
        return payload or {}

    monkeypatch.setattr(orch, "_normalize_evidence_payload", _normalize_evidence_payload)

    role = "Mechanical Systems Lead"
    title = "T"
    summary_text = "S"
    payload = [{"quotes": [{"q": "x"}]}, {"tokens_in": 7}, {"tokens_out": 11}]
    norm = _normalize_evidence_payload(payload)
    orch.evidence.add(
        role=role,
        title=title,
        summary=summary_text,
        payload=norm,
        quotes=norm.get("quotes", []),
        tokens_in=norm.get("tokens_in", 0),
        tokens_out=norm.get("tokens_out", 0),
    )
    assert added["quotes"] == [{"q": "x"}]
    assert added["tokens_in"] == 7
    assert added["tokens_out"] == 11
