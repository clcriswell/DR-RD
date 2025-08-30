import os

from utils.paths import run_root, artifact_path, ensure_run_dirs, write_bytes, write_text


def test_artifact_paths_and_writers(tmp_path):
    os.chdir(tmp_path)
    run_id = "1234567890-abcd1234"
    ensure_run_dirs(run_id)
    root = run_root(run_id)
    assert root.exists()
    bpath = write_bytes(run_id, "trace", "json", b"{}");
    assert bpath == artifact_path(run_id, "trace", "json")
    assert bpath.read_bytes() == b"{}"
    tpath = write_text(run_id, "report", "md", "hi")
    assert tpath.read_text() == "hi"
