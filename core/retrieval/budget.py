from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Iterable, Mapping, Optional


def first_valid_int(values: Iterable[object]) -> Optional[int]:
    """Return the first value that can be coerced to int."""
    for v in values:
        if v in (None, ""):
            continue
        try:
            return int(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
    return None


def get_web_max_calls(env: Mapping[str, str], mode_cfg: Mapping[str, object]) -> int:
    """Normalize the web-search call cap from config and environment.

    Preference order:

    1. ``mode_cfg['web_search_max_calls']``
    2. ``env['WEB_SEARCH_MAX_CALLS']``
    3. ``env['LIVE_SEARCH_MAX_CALLS']`` (legacy)

    If none are set or the resolved value is ``<= 0`` while no vector index is
    available, default to ``3`` to keep web search usable in web-only mode.
    """

    candidate = first_valid_int(
        [
            mode_cfg.get("web_search_max_calls"),
            mode_cfg.get("live_search_max_calls"),
            env.get("WEB_SEARCH_MAX_CALLS"),
            env.get("LIVE_SEARCH_MAX_CALLS"),
        ]
    )
    if candidate is None:
        return 3
    if int(candidate) <= 0 and not mode_cfg.get("vector_index_present"):
        return 3
    return int(candidate)


def get_web_search_call_cap(cfg: Mapping[str, object]) -> int:
    """Backward-compatible wrapper for older call sites."""

    return get_web_max_calls(os.environ, cfg)


# Backwards compatibility -----------------------------------------------------------------

# Some tests/imports still reference the old name. Provide a thin wrapper so existing
# callers continue to work without modification. The wrapper intentionally ignores the
# second ``env`` argument that used to be required.
def get_web_search_max_calls(cfg: Mapping[str, object], _env: Mapping[str, str] | None = None) -> int:
    return get_web_search_call_cap(cfg)


@dataclass
class RetrievalBudget:
    """Track web-search usage against a call cap."""

    max_calls: int
    used: int = 0

    def allow(self) -> bool:
        return self.max_calls <= 0 or self.used < self.max_calls

    def consume(self) -> None:
        self.used += 1


RETRIEVAL_BUDGET: RetrievalBudget | None = None
