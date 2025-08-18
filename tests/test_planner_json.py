from utils.json_safety import parse_json_loose


def test_strip_code_fences_and_parse():
    raw = "```json\n{\"CTO\":[{\"title\":\"Arch\",\"description\":\"Do X\"}]}\n```"
    obj = parse_json_loose(raw)
    assert "CTO" in obj and isinstance(obj["CTO"], list)


def test_recover_from_trailing_commas():
    raw = "{ \"CTO\": [ {\"title\":\"A\",\"description\":\"B\",}, ], }"
    obj = parse_json_loose(raw)
    assert obj["CTO"][0]["title"] == "A"
