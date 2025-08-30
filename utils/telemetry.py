from pathlib import Path
import json
import os
import time

LOG_DIR = Path(os.getenv("TELEMETRY_LOG_DIR", ".dr_rd/telemetry"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "events.jsonl"


def log_event(ev: dict) -> None:
    ev.setdefault("ts", time.time())
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
