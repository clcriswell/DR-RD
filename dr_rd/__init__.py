"""Top-level package for dr-rd."""

from importlib import metadata as _metadata


def get_version() -> str:
    """Return the installed package version."""
    try:
        return _metadata.version("dr-rd")
    except _metadata.PackageNotFoundError:  # pragma: no cover - during local dev
        return "0.0.0"


__version__ = get_version()

__all__ = ["__version__", "get_version"]

