from core.privacy import redact_for_logging, pseudonymize_for_model, rehydrate_output


def test_roles_preserved_and_pii_redacted():
    text = "CTO Jane Doe <jane@example.com>"
    red = redact_for_logging(text)
    assert "CTO" in red
    assert "Jane" not in red and "example.com" not in red


def test_pseudonymize_roundtrip():
    payload = {"name": "Jane Doe", "email": "jane@example.com"}
    pseudo, mapping = pseudonymize_for_model(payload)
    assert "Jane" not in str(pseudo)
    restored = rehydrate_output(pseudo, mapping)
    assert restored == payload
