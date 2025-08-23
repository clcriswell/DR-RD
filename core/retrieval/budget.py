from __future__ import annotations

from dataclasses import dataclass
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


def get_web_search_call_cap(cfg: Mapping[str, object]) -> int:
    """Return the normalized web-search call cap.

    Preference order:

    1. ``cfg['web_search_max_calls']``
    2. ``cfg['live_search_max_calls']``
    3. Fallback to ``3``

    This keeps a single source of truth for the cap and avoids subtle
    divergence between different parts of the codebase.
    """

    candidate = first_valid_int(
        [cfg.get("web_search_max_calls"), cfg.get("live_search_max_calls")]
    )
    if candidate is None:
        return 3
    return int(candidate)


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
