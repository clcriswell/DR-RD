import core.orchestrator as orch


def test_normalize_payload_list_quotes_tokens():
    added = {}

    class DummyEvidence:
        def add(self, **kw):
            added.update(kw)

    orch.evidence = DummyEvidence()

    payload = [{"quotes": [{"q": "x"}]}, {"tokens_in": 7}, {"tokens_out": 11}]
    norm = orch._normalize_evidence_payload(payload)
    orch.evidence.add(
        role="Mechanical Systems Lead",
        title="T",
        summary="S",
        payload=norm,
        quotes=norm.get("quotes", []),
        tokens_in=norm.get("tokens_in", 0),
        tokens_out=norm.get("tokens_out", 0),
    )
    assert added["quotes"] == [{"q": "x"}]
    assert added["tokens_in"] == 7
    assert added["tokens_out"] == 11
