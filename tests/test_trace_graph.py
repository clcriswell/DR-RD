from utils.graph.trace_graph import build_graph, critical_path, to_dot


def test_build_and_critical_path():
    trace = [
        {"i": 1, "phase": "plan", "name": "a", "status": "success", "duration_ms": 10},
        {"i": 2, "phase": "plan", "name": "b", "status": "success", "duration_ms": 20},
        {
            "i": 3,
            "phase": "exec",
            "name": "c",
            "status": "warn",
            "duration_ms": 30,
            "parents": ["s2"],
        },
        {"i": 4, "phase": "exec", "name": "d", "status": "error", "duration_ms": 40},
        {
            "i": 5,
            "phase": "synth",
            "name": "e",
            "status": "success",
            "duration_ms": 50,
            "parents": ["s4"],
        },
    ]
    nodes, edges = build_graph(trace)
    assert len(nodes) == 5
    assert len(edges) == 4

    path = critical_path(nodes, edges)
    assert path == ["s1", "s2", "s3", "s4", "s5"]

    dot = to_dot(nodes, edges, highlight=path)
    assert 'label="plan"' in dot
    assert '"s3"' in dot


def test_critical_path_empty_graph_returns_empty_list():
    assert critical_path([], []) == []
