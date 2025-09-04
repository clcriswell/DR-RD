from pathlib import Path

from utils import trace_writer


def test_trace_path_is_run_scoped():
    run_id = "abc123"
    p = trace_writer.trace_path(run_id)
    assert p == Path(".dr_rd") / "runs" / run_id / "trace.json"

