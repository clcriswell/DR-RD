import pytest

segmenter = pytest.importorskip("planning.segmenter")
load_redaction_policy = getattr(segmenter, "load_redaction_policy", None)
redact_text = getattr(segmenter, "redact_text", None)
if load_redaction_policy is None or redact_text is None:  # pragma: no cover - optional feature
    pytest.skip("redaction utilities not available", allow_module_level=True)


def test_ipv6_and_address_redaction_idempotent(monkeypatch):
    monkeypatch.setenv("DRRD_ENABLE_PROMPT_REDACTION", "1")
    policy = load_redaction_policy()
    text = "Reach me at 2001:0db8:85a3:0000:0000:8a2e:0370:7334\n123 Main St"  # IPv6 and address
    red1 = redact_text(policy, text)
    red2 = redact_text(policy, red1)
    assert red1 == red2
    assert "[REDACTED:IPV6]" in red1
    assert "[REDACTED:ADDRESS]" in red1
