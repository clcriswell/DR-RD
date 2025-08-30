import json
import os
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


def get(
    name: str, cast: Callable[[str], T] | None = None, *, default: Optional[T] = None
) -> Optional[T]:
    """Resolve secret by precedence: env var → st.secrets → default.

    Parameters
    ----------
    name: Secret name.
    cast: Optional callable applied to the secret value. If it raises, the
        default is returned instead.
    default: Value returned when the secret is missing or cast fails.
    """
    v: Optional[str] | None = os.getenv(name)
    if v is None:
        try:  # lazy import to avoid heavy Streamlit dependency
            import streamlit as st  # type: ignore

            sv = st.secrets.get(name)
            if sv is not None:
                v = sv if isinstance(sv, str) else json.dumps(sv)
        except Exception:
            v = None
    if v is None:
        return default
    if cast:
        try:
            return cast(v)
        except Exception:
            return default
    return v  # type: ignore[return-value]


def require(name: str) -> str:
    v = get(name)
    if not v:
        raise RuntimeError(f"missing secret: {name}")
    return v
