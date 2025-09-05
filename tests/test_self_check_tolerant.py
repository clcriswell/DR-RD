import json

from core.evaluation.self_check import validate_and_retry


def test_self_check_repairs_trailing_comma():
    text = (
        "```json {\"role\":\"r\",\"task\":\"t\",\"findings\":[1],"
        "\"risks\":[2],\"next_steps\":[3],\"sources\":[],} ```"
    )
    result, meta = validate_and_retry("r", {"id": 1, "title": "t"}, text, lambda _: text)
    assert meta["valid_json"] is True
    parsed = json.loads(result)
    assert parsed["role"] == "r"


def test_self_check_returns_structured_failure():
    bad = "not json"
    result, meta = validate_and_retry("r", {"id": 1, "title": "t"}, bad, lambda _: bad)
    assert meta["valid_json"] is False
    assert result["valid_json"] is False
    assert "raw_head" in result
