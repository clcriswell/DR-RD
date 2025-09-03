from utils import paths, trace_writer


def test_trace_atomic_creation(tmp_path):
    paths.RUNS_ROOT = tmp_path / ".dr_rd" / "runs"
    step = {"phase": "executor", "event": "x"}
    trace_writer.append_step("", step)
    assert (paths.RUNS_ROOT / "trace.json").exists()
