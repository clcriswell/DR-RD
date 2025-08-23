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


def get_web_search_max_calls(resolved_cfg: dict, env: Mapping[str, str]) -> int:
    """Resolve the web-search call cap from env and config."""
    candidates = [
        env.get("WEB_SEARCH_MAX_CALLS"),
        env.get("LIVE_SEARCH_MAX_CALLS"),
        resolved_cfg.get("web_search_max_calls"),
        resolved_cfg.get("live_search_max_calls"),
    ]
    max_calls = first_valid_int(candidates)
    web_only = (
        resolved_cfg.get("live_search_enabled") is True
        and not resolved_cfg.get("vector_index_present", False)
    )
    if (not max_calls or max_calls <= 0) and web_only:
        return 3
    return int(max_calls or 0)


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
