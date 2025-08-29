#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

from dr_rd.ops import slo, alerts


def main() -> int:
    log_dir = Path(os.getenv("TELEMETRY_LOG_DIR", ".dr_rd/telemetry"))
    paths = sorted(log_dir.glob("*.jsonl"))
    events = slo.load_events(paths)
    cfg_path = Path("config/slo.yaml")
    targets = {}
    if cfg_path.exists():
        import yaml

        with open(cfg_path, "r", encoding="utf-8") as fh:
            targets = yaml.safe_load(fh) or {}
    summary = slo.compute_slo(events, targets)
    report = alerts.evaluate(summary, targets.get("slos", {}))
    print(json.dumps(report, indent=2))
    return 1 if report.get("breaches") else 0


if __name__ == "__main__":
    raise SystemExit(main())
