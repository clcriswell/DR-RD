from utils.redaction import load_policy, redact_text

policy = load_policy("config/redaction.yaml")


def test_each_pattern():
    text = "Contact john.doe@example.com or 555-123-4567, SSN 123-45-6789, card 4111 1111 1111 1111, ip 192.168.0.1, name Jane Doe, address 123 Main St"
    redacted = redact_text(text, policy=policy)
    assert "[REDACTED:EMAIL]" in redacted
    assert "[REDACTED:PHONE]" in redacted
    assert "[REDACTED:SSN]" in redacted
    assert "[REDACTED:CREDIT_CARD]" in redacted
    assert "[REDACTED:IPV4]" in redacted
    assert "[REDACTED:NAME]" in redacted
    assert "[REDACTED:ADDRESS]" in redacted


def test_idempotent():
    text = "john.doe@example.com"
    r1 = redact_text(text, policy=policy)
    r2 = redact_text(r1, policy=policy)
    assert r1 == r2
