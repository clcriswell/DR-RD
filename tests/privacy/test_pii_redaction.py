from dr_rd.privacy import pii


def test_redact_text_and_json():
    token = "[X]"
    text = "Email a@example.com and phone 555-123-4567"
    red = pii.redact_text(text, token)
    assert "a@example.com" not in red and token in red
    data = {"user": {"email": "a@example.com", "nums": ["555-123-4567"]}}
    red_json = pii.redact_json(data, token)
    assert red_json["user"]["email"] == token
    assert red_json["user"]["nums"][0] == token
