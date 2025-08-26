from app.agent_trace_ui import _format_summary


def test_format_summary_handles_dict():
    payload = {"content": "First line\nSecond line"}
    result = _format_summary(payload)
    assert result == "First line"
