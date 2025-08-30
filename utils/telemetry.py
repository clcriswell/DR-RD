from pathlib import Path
import json
import os
import time

LOG_DIR = Path(os.getenv("TELEMETRY_LOG_DIR", ".dr_rd/telemetry"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "events.jsonl"


def log_event(ev: dict) -> None:
    ev.setdefault("ts", time.time())
    try:
        line = json.dumps(ev, ensure_ascii=False)
    except Exception:
        return
    try:
        with LOG_PATH.open("a", encoding="utf-8", errors="ignore") as f:
            f.write(line + "\n")
    except OSError:
        pass


def run_cancel_requested(run_id: str) -> None:
    """Emit a run_cancel_requested telemetry event."""
    log_event({"event": "run_cancel_requested", "run_id": run_id})


def run_cancelled(run_id: str, phase: str | None = None) -> None:
    """Emit a run_cancelled telemetry event."""
    ev = {"event": "run_cancelled", "run_id": run_id}
    if phase:
        ev["phase"] = phase
    log_event(ev)


def timeout_hit(run_id: str, phase: str | None = None) -> None:
    """Emit a timeout_hit telemetry event."""
    ev = {"event": "timeout_hit", "run_id": run_id}
    if phase:
        ev["phase"] = phase
    log_event(ev)
