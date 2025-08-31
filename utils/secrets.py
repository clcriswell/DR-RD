from typing import Callable, Optional, TypeVar

from dr_rd.config.env import get_env, require_env

T = TypeVar("T")

def get(
    name: str,
    cast: Callable[[str], T] | None = None,
    *,
    default: Optional[T] = None,
) -> Optional[T]:
    """Resolve secret by precedence: env var → st.secrets → default."""
    v = get_env(name)
    if v is None:
        return default
    if cast:
        try:
            return cast(v)
        except Exception:
            return default
    return v  # type: ignore[return-value]

def require(name: str) -> str:
    """Return secret or raise RuntimeError if missing."""
    return require_env(name)
