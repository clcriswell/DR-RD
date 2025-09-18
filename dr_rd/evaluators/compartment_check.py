from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable as IterableABC, Mapping as MappingABC
from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


_REDACTION_TOKEN = "[REDACTED_SCOPE]"


@dataclass(frozen=True)
class _Rule:
    pattern: re.Pattern[str]
    reason: str
    label: str | None = None


_IDEA_RULES: tuple[_Rule, ...] = (
    _Rule(re.compile(r"\bidea\s*:", re.IGNORECASE), "idea_reference"),
    _Rule(re.compile(r"\boverall\s+idea\b", re.IGNORECASE), "idea_reference"),
    _Rule(re.compile(r"\bproject\s+idea\b", re.IGNORECASE), "idea_reference"),
    _Rule(re.compile(r"\bglobal\s+idea\b", re.IGNORECASE), "idea_reference"),
    _Rule(re.compile(r"\bcentral\s+idea\b", re.IGNORECASE), "idea_reference"),
)


_ROLE_RULES: tuple[_Rule, ...] = (
    _Rule(re.compile(r"\bplanner\b", re.IGNORECASE), "cross_role_reference", "Planner"),
    _Rule(re.compile(r"\bcto\b", re.IGNORECASE), "cross_role_reference", "CTO"),
    _Rule(
        re.compile(r"\bregulatory(?:\s+agent|\s+team)?\b", re.IGNORECASE),
        "cross_role_reference",
        "Regulatory",
    ),
    _Rule(
        re.compile(r"\bfinance(?:\s+agent|\s+team)?\b", re.IGNORECASE),
        "cross_role_reference",
        "Finance",
    ),
    _Rule(
        re.compile(r"\bmarketing\s+analyst\b", re.IGNORECASE),
        "cross_role_reference",
        "Marketing Analyst",
    ),
    _Rule(
        re.compile(r"\bmarketing\s+agent\b", re.IGNORECASE),
        "cross_role_reference",
        "Marketing Agent",
    ),
    _Rule(
        re.compile(r"\bip\s+analyst\b", re.IGNORECASE),
        "cross_role_reference",
        "IP Analyst",
    ),
    _Rule(
        re.compile(r"\bpatent(?:\s+agent|\s+team)?\b", re.IGNORECASE),
        "cross_role_reference",
        "Patent",
    ),
    _Rule(
        re.compile(r"\bresearch\s+scientist\b", re.IGNORECASE),
        "cross_role_reference",
        "Research Scientist",
    ),
    _Rule(re.compile(r"\bhrm\b", re.IGNORECASE), "cross_role_reference", "HRM"),
    _Rule(
        re.compile(r"\bmaterials\s+engineer\b", re.IGNORECASE),
        "cross_role_reference",
        "Materials Engineer",
    ),
    _Rule(
        re.compile(r"\bdynamic\s+specialist\b", re.IGNORECASE),
        "cross_role_reference",
        "Dynamic Specialist",
    ),
    _Rule(re.compile(r"\bqa(?:\s+agent)?\b", re.IGNORECASE), "cross_role_reference", "QA"),
    _Rule(re.compile(r"\bsynthesizer\b", re.IGNORECASE), "cross_role_reference", "Synthesizer"),
)


def _dedupe_terms(terms: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for term in terms:
        if term is None:
            continue
        text = str(term).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
    return cleaned


def _extract_keywords(text: str) -> list[str]:
    if not text:
        return []
    normalized = re.sub(r"[^A-Za-z0-9\s\-_/]", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized:
        return []
    tokens = [token for token in re.split(r"[\s\-_/]+", normalized) if token]
    keywords: list[str] = []
    if len(normalized) > 3:
        keywords.append(normalized)
    for token in tokens:
        if len(token) > 3:
            keywords.append(token)
    max_ngram = min(3, len(tokens))
    for size in range(2, max_ngram + 1):
        for start in range(0, len(tokens) - size + 1):
            segment = " ".join(tokens[start : start + size])
            if len(segment) > 3:
                keywords.append(segment)
    return _dedupe_terms(keywords)


def _term_to_pattern(term: str) -> re.Pattern[str] | None:
    cleaned = term.strip()
    if not cleaned:
        return None
    pieces = [re.escape(part) for part in re.split(r"[\s\-_/]+", cleaned) if part]
    if not pieces:
        return None
    if len(pieces) == 1:
        body = pieces[0]
        return re.compile(rf"(?<!\w){body}(?!\w)", re.IGNORECASE)
    body = r"[\s\-_/]*".join(pieces)
    return re.compile(rf"(?<!\w){body}(?!\w)", re.IGNORECASE)


def _build_term_rules(terms: Iterable[str], reason: str) -> list[_Rule]:
    rules: list[_Rule] = []
    for term in _dedupe_terms(terms):
        pattern = _term_to_pattern(term)
        if pattern is None:
            continue
        rules.append(_Rule(pattern, reason, term))
    return rules


def _format_path(path: tuple[str, ...]) -> str:
    if not path:
        return "$"
    formatted = "$"
    for part in path:
        if part.isdigit():
            formatted += f"[{part}]"
        else:
            formatted += f".{part}"
    return formatted


def _iter_strings(payload: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], str]]:
    if isinstance(payload, str):
        yield path, payload
        return
    if isinstance(payload, MappingABC):
        for key, value in payload.items():
            yield from _iter_strings(value, path + (str(key),))
        return
    if isinstance(payload, (list, tuple)):
        for idx, item in enumerate(payload):
            yield from _iter_strings(item, path + (str(idx),))
        return
    if payload is not None:
        text = str(payload)
        if text:
            yield path, text


def _scan(
    payload: Any,
    rules: Sequence[_Rule],
    current_role: str,
) -> tuple[list[dict[str, Any]], dict[tuple[str, ...], list[re.Pattern[str]]]]:
    matches: list[dict[str, Any]] = []
    redactions: dict[tuple[str, ...], list[re.Pattern[str]]] = defaultdict(list)
    seen: set[tuple[tuple[str, ...], str, str]] = set()
    current = current_role.lower()
    for path, text in _iter_strings(payload):
        trimmed = text.strip()
        if not trimmed:
            continue
        for rule in rules:
            if rule.reason == "cross_role_reference" and rule.label and current:
                if rule.label.lower() == current:
                    continue
            match = rule.pattern.search(trimmed)
            if not match:
                continue
            snippet = match.group(0)
            key = (path, rule.reason, snippet.lower())
            if key in seen:
                continue
            seen.add(key)
            entry: dict[str, Any] = {
                "reason": rule.reason,
                "pattern": rule.pattern.pattern,
                "path": _format_path(path),
                "snippet": snippet,
            }
            if rule.label:
                entry["label"] = rule.label
            if trimmed != snippet:
                entry["text"] = trimmed
            matches.append(entry)
            redactions[path].append(rule.pattern)
    return matches, redactions


def _redact_payload(
    value: Any,
    redactions: Mapping[tuple[str, ...], Sequence[re.Pattern[str]]],
    path: tuple[str, ...] = (),
) -> Any:
    if isinstance(value, str):
        sanitized = value
        for pattern in redactions.get(path, []):
            sanitized = pattern.sub(_REDACTION_TOKEN, sanitized)
        return sanitized
    if isinstance(value, list):
        return [
            _redact_payload(item, redactions, path + (str(idx),))
            for idx, item in enumerate(value)
        ]
    if isinstance(value, tuple):
        return tuple(
            _redact_payload(item, redactions, path + (str(idx),))
            for idx, item in enumerate(value)
        )
    if isinstance(value, MappingABC):
        return {
            key: _redact_payload(val, redactions, path + (str(key),))
            for key, val in value.items()
        }
    return value


def evaluate(payload: Any, config: Mapping[str, Any] | None = None) -> tuple[bool, str, dict[str, Any]]:
    context = dict(config or {})
    idea_terms: list[str] = []
    for key in ("idea_terms", "idea_forbidden_terms", "forbidden_terms"):
        value = context.get(key)
        if isinstance(value, str):
            idea_terms.append(value)
        elif isinstance(value, MappingABC):
            idea_terms.extend(str(item) for item in value.values() if item is not None)
        elif isinstance(value, IterableABC):
            idea_terms.extend(str(item) for item in value if item is not None)
    idea_value = context.get("idea")
    if isinstance(idea_value, str):
        idea_terms.extend(_extract_keywords(idea_value))

    role_terms: list[str] = []
    for key in ("role_names", "roles", "forbidden_roles"):
        value = context.get(key)
        if isinstance(value, str):
            role_terms.append(value)
        elif isinstance(value, MappingABC):
            role_terms.extend(str(item) for item in value.values() if item is not None)
        elif isinstance(value, IterableABC):
            role_terms.extend(str(item) for item in value if item is not None)

    current_role = str(context.get("current_role") or "").strip()

    rules: list[_Rule] = []
    rules.extend(_IDEA_RULES)
    rules.extend(_build_term_rules(idea_terms, "idea_reference"))
    rules.extend(_ROLE_RULES)
    rules.extend(_build_term_rules(role_terms, "cross_role_reference"))

    matches, redactions = _scan(payload, rules, current_role)
    if not matches:
        return True, "", {"action": "allow", "matches": []}

    priority = {"idea_reference": 0, "cross_role_reference": 1}
    primary_reason = min(matches, key=lambda m: priority.get(m["reason"], 99))["reason"]

    action = str(context.get("on_violation") or context.get("action") or "").strip().lower()
    if action not in {"revise", "redact"}:
        action = "revise"

    details: dict[str, Any] = {"action": action, "matches": matches}
    if action == "redact" or context.get("include_sanitized"):
        details["sanitized"] = _redact_payload(payload, redactions)

    return False, primary_reason, details


__all__ = ["evaluate"]
