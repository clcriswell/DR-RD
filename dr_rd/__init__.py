"""Top-level package for dr-rd."""

from importlib import metadata as _metadata


def get_version() -> str:
    """Return the installed package version."""
    try:
        return _metadata.version("dr-rd")
    except _metadata.PackageNotFoundError:  # pragma: no cover - during local dev
        return "0.0.0"


__version__ = get_version()

# Ensure legacy planner outputs like "Finance Specialist" resolve to the
# unified Finance role.
from core import roles as _core_roles  # noqa: E402

_core_roles.CANON.setdefault("finance specialist", "Finance")
_core_roles.CANONICAL.setdefault("Finance Specialist", "Finance")

__all__ = ["__version__", "get_version"]

