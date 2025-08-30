from utils.redaction import redact_dict, redact_text


def test_redact_text_masks():
    s = "token sk-ABCDEFGHIJKLMNOPQRST email foo@example.com"
    out = redact_text(s)
    assert "sk-" not in out
    assert "foo@example.com" not in out
    assert out.count("•••") >= 2


def test_redact_dict_clamp_and_passthrough():
    data = {"a": "sk-ABCDEFGHIJKLMNOPQRST", "b": "x" * 3000, "c": 42}
    red = redact_dict(data, max_len=100)
    assert red["a"] == "•••"
    assert len(red["b"]) <= 101  # includes ellipsis
    assert red["c"] == 42
