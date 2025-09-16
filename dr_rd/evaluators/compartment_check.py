from __future__ import annotations

import re
from typing import Any, Iterable


_IDEA_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bidea\s*:", re.IGNORECASE),
    re.compile(r"\boverall\s+idea\b", re.IGNORECASE),
    re.compile(r"\bproject\s+idea\b", re.IGNORECASE),
    re.compile(r"\bglobal\s+idea\b", re.IGNORECASE),
    re.compile(r"\bcentral\s+idea\b", re.IGNORECASE),
)


_ROLE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bplanner\b", re.IGNORECASE),
    re.compile(r"\bcto\b", re.IGNORECASE),
    re.compile(r"\bregulatory(?:\s+agent|\s+team)?\b", re.IGNORECASE),
    re.compile(r"\bfinance(?:\s+agent|\s+team)?\b", re.IGNORECASE),
    re.compile(r"\bmarketing\s+analyst\b", re.IGNORECASE),
    re.compile(r"\bmarketing\s+agent\b", re.IGNORECASE),
    re.compile(r"\bip\s+analyst\b", re.IGNORECASE),
    re.compile(r"\bpatent(?:\s+agent|\s+team)?\b", re.IGNORECASE),
    re.compile(r"\bresearch\s+scientist\b", re.IGNORECASE),
    re.compile(r"\bhrm\b", re.IGNORECASE),
    re.compile(r"\bmaterials\s+engineer\b", re.IGNORECASE),
    re.compile(r"\bdynamic\s+specialist\b", re.IGNORECASE),
    re.compile(r"\bqa(?:\s+agent)?\b", re.IGNORECASE),
    re.compile(r"\bsynthesizer\b", re.IGNORECASE),
)


def _iter_strings(payload: Any) -> Iterable[str]:
    if isinstance(payload, str):
        yield payload
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(key, str):
                yield key
            yield from _iter_strings(value)
        return
    if isinstance(payload, (list, tuple, set)):
        for item in payload:
            yield from _iter_strings(item)
        return
    if payload is not None:
        text = str(payload)
        if text:
            yield text


def _detect_idea_reference(text: str) -> bool:
    return any(pattern.search(text) for pattern in _IDEA_PATTERNS)


def _detect_role_reference(text: str) -> bool:
    return any(pattern.search(text) for pattern in _ROLE_PATTERNS)


def evaluate(payload: Any) -> tuple[bool, str]:
    for text in _iter_strings(payload):
        if _detect_idea_reference(text):
            return False, "idea_reference"
    for text in _iter_strings(payload):
        if _detect_role_reference(text):
            return False, "cross_role_reference"
    return True, ""


__all__ = ["evaluate"]
