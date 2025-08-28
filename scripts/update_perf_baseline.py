#!/usr/bin/env python
"""Update performance baseline after review."""

from __future__ import annotations

import json
from pathlib import Path

BASELINE = Path(__file__).parent / "perf_baseline.json"


def main() -> None:
    run_file = Path("perf_run.json")
    if not run_file.exists():
        raise SystemExit("perf_run.json missing")
    data = json.loads(run_file.read_text())
    BASELINE.write_text(json.dumps(data, indent=2, sort_keys=True))
    print("perf baseline updated")


if __name__ == "__main__":
    main()
