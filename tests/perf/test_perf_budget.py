import json
import random
import time
from pathlib import Path


def run_phase(delay_ms: int) -> float:
    start = time.perf_counter()
    time.sleep(delay_ms / 1000)
    return (time.perf_counter() - start) * 1000


def test_perf_budget(tmp_path):
    random.seed(42)
    phases = {
        "research": run_phase(5),
        "regulatory": run_phase(5),
        "finance": run_phase(5),
    }
    run_data = {"latency_ms": phases, "tokens_est": 0}
    run_file = Path("perf_run.json")
    run_file.write_text(json.dumps(run_data, indent=2, sort_keys=True))

    baseline = json.loads(Path("scripts/perf_baseline.json").read_text())
    for key, value in phases.items():
        assert value <= baseline["latency_ms"][key]
