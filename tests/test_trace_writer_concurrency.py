import threading
from concurrent.futures import ThreadPoolExecutor

from utils import trace_writer
from utils.paths import ensure_run_dirs


def test_append_step_concurrent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_id = ""
    ensure_run_dirs(run_id)
    barrier = threading.Barrier(5)

    def worker(i: int) -> None:
        barrier.wait()
        trace_writer.append_step(run_id, {"i": i})

    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = [ex.submit(worker, i) for i in range(5)]
        for f in futures:
            f.result()
