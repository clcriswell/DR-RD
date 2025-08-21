from core.privacy import redact_for_logging


def test_allowlist_roles():
    text = "You are the CTO AI. Contact test@example.com"
    redacted = redact_for_logging(text)
    assert "CTO" in redacted
    assert "example.com" not in redacted
