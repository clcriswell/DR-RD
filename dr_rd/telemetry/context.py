import time
from contextlib import contextmanager
from typing import Any

from . import metrics


@contextmanager
def telemetry_span(name: str, **meta: Any):
    t0 = time.monotonic()
    try:
        yield
    finally:
        elapsed_ms = (time.monotonic() - t0) * 1000
        metrics.observe(f"{name}_ms", elapsed_ms, **meta)
