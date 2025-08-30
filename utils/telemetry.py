"""Telemetry logging utilities with schema validation and rotation."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from .redaction import redact_dict
from .telemetry_schema import CURRENT_SCHEMA_VERSION, upcast, validate

LOG_DIR = Path(os.getenv("TELEMETRY_LOG_DIR", ".dr_rd/telemetry"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

_LOCK = threading.Lock()
MAX_BYTES = int(os.getenv("TELEMETRY_MAX_BYTES", 25_000_000))


def _day_stamp() -> str:
    return time.strftime("%Y%m%d", time.gmtime())


def _active_path() -> Path:
    """Return the current log file path for today, rotating by size."""
    day = _day_stamp()
    base = LOG_DIR / f"events-{day}.jsonl"
    p = base
    part = 0
    while p.exists() and p.stat().st_size >= MAX_BYTES:
        part += 1
        p = LOG_DIR / f"events-{day}.part{part}.jsonl"
    return p


def _rollover(p: Path) -> Path:
    """Return next part file for the given path."""
    name = p.name
    if ".part" in name:
        prefix, rest = name.split(".part", 1)
        try:
            num = int(rest.split(".")[0]) + 1
        except ValueError:
            num = 1
        return p.with_name(f"{prefix}.part{num}.jsonl")
    return p.with_name(p.stem + ".part1.jsonl")


def log_event(ev: dict) -> None:
    """Validate, version, and append a telemetry event."""
    ev = validate(ev)
    ev.setdefault("schema_version", CURRENT_SCHEMA_VERSION)
    ev.setdefault("ts", time.time())
    ev = redact_dict(ev)
    try:
        line = json.dumps(ev, ensure_ascii=False)
    except Exception:
        return
    with _LOCK:
        p = _active_path()
        if p.exists() and p.stat().st_size + len(line) > MAX_BYTES:
            p = _rollover(p)
        lock_path = p.with_suffix(p.suffix + ".lock")
        fh = None
        try:
            try:
                fh = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except OSError:
                fh = None  # best effort
            with p.open("a", encoding="utf-8", errors="ignore") as f:
                f.write(line + "\n")
                f.flush()
        finally:
            if fh is not None:
                os.close(fh)
                try:
                    os.remove(lock_path)
                except OSError:
                    pass


def list_files(day: str | None = None) -> list[Path]:
    pattern = f"events-{day}*" if day else "events-*.jsonl"
    return sorted(LOG_DIR.glob(pattern))


def read_events(limit: int | None = None, days: int = 7) -> list[dict]:
    """Read recent events from log files.

    Parameters
    ----------
    limit: optional maximum number of events to return.
    days: how many days of logs to include, starting from today.
    """
    events: list[dict] = []
    now = time.time()
    for i in range(days):
        day = time.strftime("%Y%m%d", time.gmtime(now - i * 86400))
        files = list_files(day)
        for p in files:
            try:
                with p.open("r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        try:
                            ev = json.loads(line)
                            ev = upcast(ev)
                            events.append(ev)
                        except Exception:
                            continue
                        if limit and len(events) >= limit:
                            return events
            except OSError:
                continue
    return events


# Convenience event wrappers remain largely unchanged below.


def llm_call_started(provider: str, model: str, attempt: int, run_id: str | None = None, step_id: str | None = None) -> None:
    ev = {"event": "llm_call_started", "provider": provider, "model": model, "attempt": attempt}
    if run_id:
        ev["run_id"] = run_id
    if step_id:
        ev["step_id"] = step_id
    log_event(ev)


def llm_call_succeeded(provider: str, model: str, attempt: int, run_id: str | None = None, step_id: str | None = None) -> None:
    ev = {"event": "llm_call_succeeded", "provider": provider, "model": model, "attempt": attempt}
    if run_id:
        ev["run_id"] = run_id
    if step_id:
        ev["step_id"] = step_id
    log_event(ev)


def llm_call_failed(provider: str, model: str, attempt: int, kind: str, run_id: str | None = None, step_id: str | None = None) -> None:
    ev = {"event": "llm_call_failed", "provider": provider, "model": model, "attempt": attempt, "kind": kind}
    if run_id:
        ev["run_id"] = run_id
    if step_id:
        ev["step_id"] = step_id
    log_event(ev)


def llm_fallback(provider: str, model: str, run_id: str | None = None, step_id: str | None = None) -> None:
    ev = {"event": "llm_fallback", "provider": provider, "model": model}
    if run_id:
        ev["run_id"] = run_id
    if step_id:
        ev["step_id"] = step_id
    log_event(ev)


def llm_cache_hit(provider: str, model: str, run_id: str | None = None, step_id: str | None = None) -> None:
    ev = {"event": "llm_cache_hit", "provider": provider, "model": model}
    if run_id:
        ev["run_id"] = run_id
    if step_id:
        ev["step_id"] = step_id
    log_event(ev)


def circuit_skipped(provider: str, model: str) -> None:
    log_event({"event": "circuit_skipped", "provider": provider, "model": model})


def flag_checked(name: str, value: bool) -> None:
    if os.getenv("TELEMETRY_DEBUG") == "1":
        log_event({"event": "flag_checked", "flag": name, "value": value})


def exp_exposed(user_id_hash: str, exp_id: str, variant: str, run_id: str | None = None) -> None:
    ev = {"event": "exp_exposed", "user_id": user_id_hash, "exp_id": exp_id, "variant": variant}
    if run_id:
        ev["run_id"] = run_id
    log_event(ev)


def exp_overridden(exp_id: str, variant: str) -> None:
    log_event({"event": "exp_overridden", "exp_id": exp_id, "variant": variant})


def run_cancel_requested(run_id: str) -> None:
    """Emit a run_cancel_requested telemetry event."""
    log_event({"event": "run_cancel_requested", "run_id": run_id})


def run_cancelled(run_id: str, phase: str | None = None) -> None:
    """Emit a run_cancelled telemetry event."""
    ev = {"event": "run_cancelled", "run_id": run_id}
    if phase:
        ev["phase"] = phase
    log_event(ev)


def stream_started(run_id: str) -> None:
    """Emit a stream_started telemetry event."""
    log_event({"event": "stream_started", "run_id": run_id})


def stream_chunked(run_id: str, tokens: int) -> None:
    """Emit a stream_chunked telemetry event."""
    log_event({"event": "stream_chunked", "run_id": run_id, "tokens": tokens})


def stream_completed(run_id: str, status: str) -> None:
    """Emit a stream_completed telemetry event."""
    log_event({"event": "stream_completed", "run_id": run_id, "status": status})


def run_lock_acquired(run_id: str) -> None:
    """Emit a run_lock_acquired telemetry event."""
    log_event({"event": "run_lock_acquired", "run_id": run_id})


def run_lock_released(run_id: str) -> None:
    """Emit a run_lock_released telemetry event."""
    log_event({"event": "run_lock_released", "run_id": run_id})


def run_start_blocked(reason: str, run_id: str | None = None) -> None:
    """Emit a run_start_blocked telemetry event."""
    ev = {"event": "run_start_blocked", "reason": reason}
    if run_id:
        ev["run_id"] = run_id
    log_event(ev)


def run_duplicate_detected(run_id: str) -> None:
    """Emit a run_duplicate_detected telemetry event."""
    log_event({"event": "run_duplicate_detected", "run_id": run_id})


def checkpoint_saved(run_id: str, phase: str, step_id: str | int) -> None:
    """Emit a checkpoint_saved telemetry event."""
    log_event({"event": "checkpoint_saved", "run_id": run_id, "phase": phase, "step_id": step_id})


def run_resumed(new_run_id: str, origin_run_id: str) -> None:
    """Emit a run_resumed telemetry event."""
    log_event({"event": "run_resumed", "new_run_id": new_run_id, "origin_run_id": origin_run_id})


def resume_failed(origin_run_id: str, reason: str) -> None:
    """Emit a resume_failed telemetry event."""
    log_event({"event": "resume_failed", "origin_run_id": origin_run_id, "reason": reason})


def timeout_hit(run_id: str, phase: str | None = None) -> None:
    """Emit a timeout_hit telemetry event."""
    ev = {"event": "timeout_hit", "run_id": run_id}
    if phase:
        ev["phase"] = phase
    log_event(ev)


def demo_started(run_id: str) -> None:
    """Emit a demo_started telemetry event."""
    log_event({"event": "demo_started", "run_id": run_id})


def demo_completed(run_id: str) -> None:
    """Emit a demo_completed telemetry event."""
    log_event({"event": "demo_completed", "run_id": run_id})


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


def knowledge_added(item_id: str, name: str, type_: str, size: int) -> None:
    """Emit a knowledge_added telemetry event."""
    log_event(
        {"event": "knowledge_added", "id": item_id, "name": name, "type": type_, "size": size}
    )


def knowledge_removed(item_id: str) -> None:
    """Emit a knowledge_removed telemetry event."""
    log_event({"event": "knowledge_removed", "id": item_id})


def knowledge_tags_updated(item_id: str, count: int) -> None:
    """Emit a knowledge_tags_updated telemetry event."""
    log_event({"event": "knowledge_tags_updated", "id": item_id, "count": count})


def history_filter_changed(q_len: int, status_count: int, mode_count: int, fav: bool) -> None:
    """Emit a history_filter_changed telemetry event."""
    log_event(
        {
            "event": "history_filter_changed",
            "q_len": q_len,
            "status_count": status_count,
            "mode_count": mode_count,
            "fav": bool(fav),
        }
    )


def history_export_clicked(count: int) -> None:
    """Emit a history_export_clicked telemetry event."""
    log_event({"event": "history_export_clicked", "count": count})


def run_annotated(
    run_id: str, title_len: int, tags_count: int, note_len: int, favorite: bool
) -> None:
    """Emit a run_annotated telemetry event."""
    log_event(
        {
            "event": "run_annotated",
            "run_id": run_id,
            "title_len": title_len,
            "tags_count": tags_count,
            "note_len": note_len,
            "favorite": bool(favorite),
        }
    )


def run_favorited(run_id: str, favorite: bool) -> None:
    """Emit a run_favorited telemetry event."""
    log_event({"event": "run_favorited", "run_id": run_id, "favorite": bool(favorite)})


__all__ = [
    "log_event",
    "list_files",
    "read_events",
    "run_cancel_requested",
    "run_cancelled",
    "stream_started",
    "stream_chunked",
    "stream_completed",
    "timeout_hit",
    "demo_started",
    "demo_completed",
    "flag_checked",
    "exp_exposed",
    "exp_overridden",
    "checkpoint_saved",
    "run_resumed",
    "resume_failed",
    "usage_threshold_crossed",
    "usage_exceeded",
    "knowledge_added",
    "knowledge_removed",
    "knowledge_tags_updated",
    "history_filter_changed",
    "history_export_clicked",
    "run_annotated",
    "run_favorited",
]
