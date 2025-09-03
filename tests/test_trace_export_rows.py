from utils.trace_export import flatten_trace_rows


def test_flatten_trace_rows():
    trace = [
        {
            "phase": "plan",
            "name": "a",
            "status": "complete",
            "duration_ms": 1,
            "tokens": 2,
            "cost": 0.3,
            "summary": "ok",
        },
        {"phase": "exec", "name": "b", "status": "error"},
    ]
    rows = flatten_trace_rows(trace)
    assert len(rows) == 2
    assert rows[0]["i"] == 1
    assert rows[1]["status"] == "error"
    assert set(rows[0].keys()) == {
        "i",
        "id",
        "parents",
        "phase",
        "name",
        "status",
        "duration_ms",
        "tokens",
        "cost",
        "summary",
        "prompt",
        "citations",
        "planned_tasks",
        "normalized_tasks",
        "routed_tasks",
        "empty_fields",
        "exec_tasks",
    }
