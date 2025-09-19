"""Utilities for neutralizing idea-specific terms in prompts."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, MutableMapping
from typing import Any

from dr_rd.prompting.planner_specificity import ensure_plan_task_specificity

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
        sanitized, replaced = neutralize_project_terms(idea_value, alias)
        inputs["idea"] = sanitized
        existing = inputs.get("idea_forbidden_terms")
        combined = []
        if isinstance(existing, list):
            combined.extend(item for item in existing if isinstance(item, str))
        combined.extend(replaced)
        inputs["idea_forbidden_terms"] = _dedupe(combined)
    inputs.setdefault("idea_alias", alias)


def _expand_forbidden_terms(terms: Iterable[str], alias: str) -> list[str]:
    expanded: list[str] = []
    for term in terms:
        if not term:
            continue
        cleaned = str(term).strip()
        if not cleaned:
            continue
        expanded.append(cleaned)
        pieces = [p for p in re.split(r"[\s\-_/]+", cleaned) if p]
        if len(pieces) > 1:
            for size in range(1, len(pieces) + 1):
                for start in range(0, len(pieces) - size + 1):
                    segment = " ".join(pieces[start : start + size]).strip()
                    if segment and len(segment) > 3:
                        expanded.append(segment)
        else:
            part = pieces[0] if pieces else cleaned
            if len(part) > 3:
                expanded.append(part)

    seen: set[str] = set()
    result: list[str] = []
    for term in expanded:
        key = term.lower()
        if key == alias.lower():
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(term)
    return result


def _neutralize_explicit_terms(text: str, terms: Iterable[str], alias: str) -> tuple[str, bool]:
    if not text or not terms:
        return text, False

    pattern_parts = []
    for term in terms:
        if not term:
            continue
        escaped = re.escape(term)
        pattern_parts.append(rf"\b{escaped}\b")
    if not pattern_parts:
        return text, False

    pattern = re.compile("|".join(sorted(pattern_parts, key=len, reverse=True)), re.IGNORECASE)

    replaced = False

    def _sub(match: re.Match[str]) -> str:
        nonlocal replaced
        replaced = True
        prefix = text[: match.start()]
        alias_token = _normalize_alias(alias, not prefix.strip())
        return alias_token

    sanitized = pattern.sub(_sub, text)
    if not replaced:
        return text, False

    sanitized = re.sub(r"\b(a|an|the)\s+the system\b", "the system", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bthe\s+the system\b", "the system", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bthe system\s+the system\b", "the system", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\s{2,}", " ", sanitized).strip()
    return sanitized, True


def sanitize_planner_plan(
    plan: Any,
    forbidden_terms: Iterable[str],
    alias: str = NEUTRAL_ALIAS,
) -> tuple[Any, bool]:
    terms = _expand_forbidden_terms(forbidden_terms, alias)
    changed = False

    if isinstance(plan, MutableMapping):
        if ensure_plan_task_specificity(plan):
            changed = True

    if not terms:
        return plan, changed

    def _walk(value: Any) -> Any:
        nonlocal changed
        if isinstance(value, str):
            sanitized, touched = _neutralize_explicit_terms(value, terms, alias)
            if touched and sanitized != value:
                changed = True
            return sanitized
        if isinstance(value, list):
            return [_walk(item) for item in value]
        if isinstance(value, MutableMapping):
            return {key: _walk(val) for key, val in value.items()}
        return value

    sanitized_plan = _walk(plan)
    return sanitized_plan, changed


def sanitize_planner_response(
    raw: str,
    forbidden_terms: Iterable[str],
    alias: str = NEUTRAL_ALIAS,
) -> str:
    try:
        data = json.loads(raw)
    except Exception:
        return raw

    sanitized, changed = sanitize_planner_plan(data, forbidden_terms, alias)
    if not changed:
        return raw
    return json.dumps(sanitized)

