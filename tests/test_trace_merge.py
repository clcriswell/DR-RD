from core.trace.merge import merge_traces, summarize


def test_merge_and_summarize():
    graph = [{"ts": 1, "node": "n1", "phase": "start", "task_id": "t1", "duration_s": 1.0}]
    tool = [{"ts": 2, "node": "tool", "phase": "end", "task_id": "t1", "tool": "curl", "tokens": 10}]
    retrieval = [{"ts": 1.5, "node": "retr", "phase": "call", "task_id": "t1", "agent": "A"}]
    bundle = merge_traces(graph, tool, retrieval, None)
    assert [e.ts for e in bundle.events] == [1, 1.5, 2]
    summary = summarize(bundle)
    assert summary["task"]["t1"]["count"] == 3
    assert summary["task"]["t1"]["tokens"] == 10
    assert summary["agent"]["A"]["count"] == 1
