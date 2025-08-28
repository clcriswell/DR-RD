from core import provenance


def test_nested_spans_parent_child():
    provenance.reset()
    parent = provenance.start_span("parent", {"agent": "A"})
    child = provenance.start_span("child", {"tool": "T"})
    provenance.end_span(child)
    provenance.end_span(parent, ok=False)
    events = provenance.get_events()
    p = next(e for e in events if e["id"] == parent)
    c = next(e for e in events if e["id"] == child)
    assert c["parent_id"] == p["id"]
    assert p["duration_ms"] >= c["duration_ms"]
