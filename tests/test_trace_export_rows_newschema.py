from utils.trace_export import flatten_trace_rows


def test_flatten_trace_rows_new_schema():
    trace = [
        {
            "phase": "exec",
            "name": "a",
            "status": "complete",
            "tokens_in": 1,
            "tokens_out": 2,
            "cost_usd": 0.3,
        }
    ]
    rows = flatten_trace_rows(trace)
    assert rows[0]["tokens"] == 3
    assert rows[0]["cost"] == 0.3
