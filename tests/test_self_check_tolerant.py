import json

from core.evaluation.self_check import validate_and_retry


def test_self_check_tolerant_success():
    raw = "Here:\n```json\n{\"role\":\"R\",\"task\":\"t\",\"findings\":[],\"risks\":[],\"next_steps\":[],\"sources\":[]}\n```"
    fixed, meta = validate_and_retry("R", {"title": "t"}, raw, lambda r: raw)
    assert meta["valid_json"] is True
    assert json.loads(fixed)["role"] == "R"


def test_self_check_tolerant_failure():
    raw = "not json"
    fixed, meta = validate_and_retry("R", {"title": "t"}, raw, lambda r: raw)
    assert isinstance(fixed, dict)
    assert fixed["valid_json"] is False
    assert meta["valid_json"] is False
