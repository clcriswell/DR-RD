from __future__ import annotations

import os


def _flag(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).lower() == "true"


def two_pass_enabled() -> bool:
    """Return whether two-pass summarization is enabled.

    Controlled via ``SYNTH_TWO_PASS`` environment variable (default: true).
    """
    return _flag("SYNTH_TWO_PASS", "true")


def cross_reference_enabled() -> bool:
    """Return whether cross-role contradiction checks are enabled.

    Controlled via ``SYNTH_CROSS_REFERENCE`` environment variable (default: true).
    """
    return _flag("SYNTH_CROSS_REFERENCE", "true")


__all__ = ["two_pass_enabled", "cross_reference_enabled"]
