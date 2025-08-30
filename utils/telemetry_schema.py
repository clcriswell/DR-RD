"""Telemetry event schema registry and validation.

Provides minimal schema contracts for telemetry events and helpers to
validate and upcast them. The schema is intentionally permissive and
only enforces required keys for known events. Extra keys are ignored and
obvious PII fields are stripped.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

CURRENT_SCHEMA_VERSION = 1

# Basic schema definition: mapping event name -> required keys.
# Only a small subset of fields are enforced to keep things flexible.
_SCHEMAS: Dict[str, List[str]] = {
    "start_run": ["run_id"],
    "run_created": ["run_id"],
    "step_completed": ["run_id", "step"],
    "run_completed": ["run_id", "status"],
    "error_shown": ["run_id", "code"],
    "export_clicked": ["run_id", "format"],
    "nav_page_view": ["page"],
    "survey_shown": ["survey"],
    "survey_submitted": ["survey", "scores"],
    "usage_threshold_crossed": ["type", "frac"],
    "usage_exceeded": ["type"],
    "run_cancel_requested": ["run_id"],
    "run_cancelled": ["run_id"],
    "timeout_hit": ["run_id"],
    "run_resumed": ["new_run_id", "origin_run_id"],
    "checkpoint_saved": ["run_id", "phase", "step_id"],
    "demo_started": ["run_id"],
    "demo_completed": ["run_id"],
    "knowledge_added": ["id", "name", "type", "size"],
    "knowledge_removed": ["id"],
    "palette_opened": [],
    "palette_executed": ["command"],
}

# Keys that should never be persisted. This is a simple heuristic to strip
# accidental PII or user identifying information.
_PII_KEYS = {
    "email",
    "e-mail",
    "user",
    "username",
    "user_name",
    "user_id",
    "name",
    "full_name",
    "address",
    "phone",
    "ip",
    "ip_address",
}


def validate(event: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize a telemetry event.

    - Ensures the "event" key exists.
    - Attaches a ``schema_version`` and timestamp ``ts`` if missing.
    - Ensures required keys exist for known events (filling with ``None``).
    - Strips obvious PII fields.
    - Never raises on extra or malformed fields.
    """

    ev: Dict[str, Any] = dict(event or {})
    if "event" not in ev:
        ev["event"] = "unknown"

    # Drop potential PII keys.
    for key in list(ev.keys()):
        if key.lower() in _PII_KEYS:
            ev.pop(key, None)

    # Ensure required keys exist.
    required = _SCHEMAS.get(ev["event"], [])
    for key in required:
        ev.setdefault(key, None)

    # Attach metadata.
    ev.setdefault("schema_version", CURRENT_SCHEMA_VERSION)
    ev.setdefault("ts", time.time())
    return ev


def upcast(event: Dict[str, Any]) -> Dict[str, Any]:
    """Upcast an event to the ``CURRENT_SCHEMA_VERSION``.

    Currently schema version 1 has no historical versions, so this is a
    no-op other than ensuring the version is set correctly. The helper
    exists so future migrations can transform older payloads.
    """

    ev = dict(event or {})
    ver = int(ev.get("schema_version", 1))
    if ver < CURRENT_SCHEMA_VERSION:
        # In the future, transformations for older versions would go here.
        ev["schema_version"] = CURRENT_SCHEMA_VERSION
    return ev

__all__ = ["CURRENT_SCHEMA_VERSION", "validate", "upcast"]
