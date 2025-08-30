import nbformat

from utils.notebook_export import build_notebook


def test_build_notebook_basic():
    meta = {"run_id": "r1", "started_at": 0, "completed_at": 1, "status": "ok", "mode": "test"}
    lock = {"provider": "openai", "model": "gpt"}
    rows = [
        {
            "phase": "plan",
            "name": "step1",
            "status": "complete",
            "duration_ms": 10,
            "summary": "done sk-1234567890ABCDEFGHIJKLMNOP",
            "prompt": "hello",
        }
    ]
    nb_bytes = build_notebook("r1", meta, lock, rows, None)
    nb = nbformat.reads(nb_bytes.decode("utf-8"), as_version=4)
    assert nb.cells[0].source.startswith("# DR RD Run r1")
    assert any("[plan]" in c.source for c in nb.cells)
    # redaction should remove secret token
    assert "sk-" not in nb.cells[1].source

