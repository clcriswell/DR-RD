import json

from dr_rd.safety import filters


def test_pii_redaction():
    data = {"msg": "Email me at test@example.com"}
    sanitized, decision = filters.filter_output(data)
    assert "[REDACTED:email]" in sanitized["msg"]
    assert decision.allowed
    assert "pii" in decision.redactions or "pii" in decision.notes[0].lower()


def test_secrets_detection():
    data = {"msg": "openai key sk-TEST1234567890ABCDEFGHIJK"}
    sanitized, decision = filters.filter_output(data)
    assert "[REDACTED:openai]" in sanitized["msg"]
    assert not decision.allowed or "secrets" in decision.redactions
    # schema preserved
    assert set(sanitized.keys()) == {"msg"}
