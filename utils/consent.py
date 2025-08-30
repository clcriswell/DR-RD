"""User privacy consent helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import time
from typing import Optional

CONSENT_PATH = Path(".dr_rd/consent.json")


@dataclass(frozen=True)
class Consent:
    telemetry: bool
    surveys: bool
    updated_at: float


def _read() -> Optional[dict]:
    if not CONSENT_PATH.exists():
        return None
    try:
        return json.loads(CONSENT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def get() -> Consent | None:
    obj = _read()
    if not obj:
        return None
    return Consent(
        bool(obj.get("telemetry", False)),
        bool(obj.get("surveys", False)),
        float(obj.get("updated_at", 0.0)),
    )


def set(telemetry: bool, surveys: bool) -> Consent:
    CONSENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    obj = {
        "telemetry": bool(telemetry),
        "surveys": bool(surveys),
        "updated_at": time.time(),
    }
    tmp = CONSENT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CONSENT_PATH)
    return get()


def allowed_telemetry() -> bool:
    c = get()
    return bool(c and c.telemetry)


def allowed_surveys() -> bool:
    c = get()
    return bool(c and c.surveys)


__all__ = [
    "Consent",
    "get",
    "set",
    "allowed_telemetry",
    "allowed_surveys",
]

