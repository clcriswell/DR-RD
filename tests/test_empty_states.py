from app.ui import empty_states


def test_helpers_return_none_without_actions():
    assert empty_states.trace_empty() is None
    assert empty_states.reports_empty() is None
    assert empty_states.metrics_empty() is None
