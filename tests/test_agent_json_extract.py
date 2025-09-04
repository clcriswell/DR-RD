import json

from utils.agent_json import extract_json_block


def test_dict_list_passthrough():
    assert extract_json_block({"a": 1}) == {"a": 1}
    assert extract_json_block([1, 2]) == [1, 2]


def test_fenced_json():
    text = "prefix ```json {\"a\":1} ``` suffix"
    assert extract_json_block(text) == {"a": 1}


def test_loose_fallback_and_empty():
    text = "```json {\"a\":1,} ```"
    assert extract_json_block(text) == {"a": 1}
    assert extract_json_block(None) is None
    assert extract_json_block("") is None
