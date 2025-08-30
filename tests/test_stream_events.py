from utils.stream_events import Event, merge_text, is_terminal


def test_merge_text_and_terminal():
    assert merge_text("a", "b") == "ab"
    assert merge_text(None, "x") == "x"
    assert merge_text("x", None) == "x"
    assert is_terminal(Event("error"))
    assert is_terminal(Event("done"))
    assert not is_terminal(Event("token", text="hi"))
