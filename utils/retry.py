import random
import time
from typing import Callable, Tuple

DEFAULTS = dict(max_attempts=5, base=0.25, cap=8.0, jitter=0.25)

def backoff(attempt: int, *, base: float = 0.25, cap: float = 8.0, jitter: float = 0.25) -> float:
    """Return delay seconds for the given *attempt* using exponential backoff with jitter."""
    delay = min(cap, base * (2 ** max(0, attempt - 1)))
    return max(0.0, delay * (1.0 - jitter + random.random() * jitter * 2))


def classify_error(exc: Exception) -> str:
    """Return canonical error kind for provider exceptions."""
    try:
        from .errors import classify_provider_error
    except Exception:  # pragma: no cover - defensive
        classify_provider_error = None  # type: ignore
    if classify_provider_error:
        return classify_provider_error(exc)
    name = exc.__class__.__name__.lower()
    if "rate" in name and "limit" in name:
        return "rate_limit"
    if "timeout" in name:
        return "timeout"
    if "auth" in name or "key" in name:
        return "auth"
    if "quota" in name:
        return "quota"
    if isinstance(exc, (ValueError, TypeError)) or "validation" in name:
        return "validation"
    return "transient"


def should_retry(kind: str) -> bool:
    """Return True if errors of *kind* are retryable."""
    return kind in {"rate_limit", "transient", "timeout"}
