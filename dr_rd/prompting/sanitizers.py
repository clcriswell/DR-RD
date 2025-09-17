"""Utilities for neutralizing idea-specific terms in prompts."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

NEUTRAL_ALIAS = "the system"


def _dedupe(seq: Iterable[str]) -> list[str]:
    seen: list[str] = []
    for item in seq:
        if not item:
            continue
        if item not in seen:
            seen.append(item)
    return seen


def _normalize_alias(alias: str, at_start: bool) -> str:
    return alias.capitalize() if at_start else alias


def neutralize_project_terms(text: str, alias: str = NEUTRAL_ALIAS) -> tuple[str, list[str]]:
    """Replace project-specific proper nouns with a neutral alias."""

    if not text:
        return "", []

    replacements: list[str] = []
    sanitized = text

    def _replace_segment(segment: str, start: int) -> str:
        cleaned = segment.strip(" \t\n\r\f\v\"'“”‘’")
        if not cleaned:
            return segment
        lowered = cleaned.lower()
        if lowered in {alias, "the project", "project idea", "project"}:
            return segment
        replacements.append(cleaned)
        return _normalize_alias(alias, start == 0)

    header_pattern = re.compile(
        r"^\s*(?P<prefix>(?:Project\s+Idea\s*:\s*)?)(?P<name>[A-Z][\w]*(?:\s+[A-Z][\w]*){0,4})\s*(?P<sep>[:\-–—])\s*"
    )

    def _header_sub(match: re.Match[str]) -> str:
        prefix = match.group("prefix") or ""
        name = match.group("name").strip()
        sep = match.group("sep")
        if name:
            replacements.append(name)
        alias_text = _normalize_alias(alias, not bool(prefix))
        return f"{prefix}{alias_text} {sep} "

    sanitized = header_pattern.sub(_header_sub, sanitized, count=1)

    quote_pattern = re.compile(r"[\"'“”‘’]([A-Z][^\"'“”‘’]{1,60})[\"'“”‘’]")

    def _quote_sub(match: re.Match[str]) -> str:
        inner = match.group(1).strip()
        if inner:
            replacements.append(inner)
        return alias

    sanitized = quote_pattern.sub(_quote_sub, sanitized)

    camel_pattern = re.compile(r"\b([A-Z][a-z0-9]+[A-Za-z0-9]*[A-Z][A-Za-z0-9]*)\b")
    sanitized = camel_pattern.sub(lambda m: _replace_segment(m.group(0), m.start()), sanitized)

    proper_pattern = re.compile(
        r"\b([A-Z][a-zA-Z0-9]*\s+[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*)\b"
    )
    sanitized = proper_pattern.sub(lambda m: _replace_segment(m.group(0), m.start()), sanitized)

    sanitized = re.sub(r"\s{2,}", " ", sanitized)
    sanitized = re.sub(r"\b(a|an)\s+the system\b", "the system", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bthe\s+the system\b", "the system", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bthe system\s+the system\b", "the system", sanitized, flags=re.IGNORECASE)
    sanitized = sanitized.strip()

    return sanitized, _dedupe(replacements)


def apply_planner_neutralization(inputs: dict[str, Any]) -> None:
    """Mutate planner inputs so the idea briefing stays neutral."""

    alias = NEUTRAL_ALIAS
    idea_value = inputs.get("idea")
    if isinstance(idea_value, str) and idea_value.strip():
        sanitized, _ = neutralize_project_terms(idea_value, alias)
        inputs["idea"] = sanitized
    inputs.setdefault("idea_alias", alias)

