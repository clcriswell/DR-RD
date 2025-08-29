"""Deprecation helpers and shims for legacy components."""

from __future__ import annotations

import warnings
from typing import Set

_warned: Set[str] = set()


def warn_legacy_agent_use(agent_name: str, replacement: str, remove_on: str) -> None:
    """Emit a ``DeprecationWarning`` once per process for legacy agents."""
    key = f"{agent_name}:{replacement}"
    if key in _warned:
        return
    _warned.add(key)
    warnings.warn(
        f"{agent_name} is deprecated; use {replacement}. Will be removed after {remove_on}.",
        DeprecationWarning,
        stacklevel=2,
    )


__all__ = ["warn_legacy_agent_use"]
