from core.redaction import Redactor

def test_role_names_not_redacted():
    text = "CTO and Marketing Analyst reviewed"
    red, _, _ = Redactor().redact(text, mode="heavy")
    assert "CTO" in red and "Marketing Analyst" in red
