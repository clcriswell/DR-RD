from core import trace_export


def sample_events():
    return [
        {"id": "1", "name": "root", "parent_id": None, "t_start": 0, "t_end": 1, "duration_ms": 1000},
        {"id": "2", "name": "child", "parent_id": "1", "t_start": 0.1, "t_end": 0.2, "duration_ms": 100},
    ]


def test_to_tree():
    tree = trace_export.to_tree(sample_events())
    assert tree["children"][0]["children"][0]["name"] == "child"


def test_speedscope_and_chrome():
    events = sample_events()
    ss = trace_export.to_speedscope(events)
    assert ss["profiles"][0]["events"]
    ct = trace_export.to_chrometrace(events)
    assert any(e["ph"] == "X" for e in ct)
