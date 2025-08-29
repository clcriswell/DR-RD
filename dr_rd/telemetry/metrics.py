import json
import os
import time
from typing import Any, Dict

from .exporters import get_exporters
from .sampling import should_sample

TELEMETRY_ENABLED = os.getenv("TELEMETRY_ENABLED", "true").lower() == "true"
SAMPLING_RATE = float(os.getenv("TELEMETRY_SAMPLING_RATE", "1.0"))

_exporters = get_exporters()


def _emit(event: Dict[str, Any]) -> None:
    if not TELEMETRY_ENABLED:
        return
    if not should_sample(SAMPLING_RATE):
        return
    event.setdefault("timestamp", time.time())
    for exp in _exporters:
        try:
            exp.write(event)
        except Exception:
            pass


def inc(name: str, value: int = 1, **labels: Any) -> None:
    _emit({"type": "counter", "name": name, "value": int(value), "labels": labels})


def observe(name: str, value: float, **labels: Any) -> None:
    _emit({"type": "histogram", "name": name, "value": float(value), "labels": labels})


def set_gauge(name: str, value: float, **labels: Any) -> None:
    _emit({"type": "gauge", "name": name, "value": float(value), "labels": labels})
