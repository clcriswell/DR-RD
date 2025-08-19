from dr_rd.core.prompt_utils import coerce_user_content


def test_string_passthrough():
    assert coerce_user_content("x") == "x"


def test_dict_to_json():
    out = coerce_user_content({"a":1})
    assert isinstance(out, str)
    assert '"a":1' in out


def test_list_of_dicts_allowed():
    content = [{"type":"text","text":"hello"}]
    assert coerce_user_content(content) == content
