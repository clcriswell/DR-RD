import json
import os
import time
from pathlib import Path

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


def usage_threshold_crossed(
    type_: str,
    frac: float,
    run_id: str | None = None,
    *,
    phase: str | None = None,
    cost_usd: float | None = None,
    total_tokens: int | None = None,
) -> None:
    ev = {
        "event": "usage_threshold_crossed",
        "type": type_,
        "frac": frac,
    }
    if run_id:
        ev["run_id"] = run_id
    if phase:
        ev["phase"] = phase
    if cost_usd is not None:
        ev["cost_usd"] = cost_usd
    if total_tokens is not None:
        ev["total_tokens"] = total_tokens
    log_event(ev)


def usage_exceeded(
    type_: str,
    run_id: str | None = None,
    *,
    phase: str | None = None,
    cost_usd: float | None = None,
    total_tokens: int | None = None,
) -> None:
    ev = {"event": "usage_exceeded", "type": type_}
    if run_id:
        ev["run_id"] = run_id
    if phase:
        ev["phase"] = phase
    if cost_usd is not None:
        ev["cost_usd"] = cost_usd
    if total_tokens is not None:
        ev["total_tokens"] = total_tokens
    log_event(ev)


__all__ = [
    "log_event",
    "run_cancel_requested",
    "run_cancelled",
    "timeout_hit",
    "usage_threshold_crossed",
    "usage_exceeded",
]
