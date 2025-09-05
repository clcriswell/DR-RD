from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, Set

PLACEHOLDER_RE = re.compile(
    r"^\[(SECRET|EMAIL|PHONE|IPV4|IPV6|IP|ADDRESS|PERSON|ORG|DEVICE)_\d+\]$"
)

# Patterns for various categories
PATTERNS: Dict[str, Tuple[re.Pattern[str], ...]] = {
    "SECRET": (
        re.compile(r"sk-[A-Za-z0-9]{20,}"),
        re.compile(r"api_key=\w+"),
        re.compile(r"-----BEGIN(?:[ A-Z]+)?PRIVATE KEY-----[\s\S]+?-----END(?:[ A-Z]+)?PRIVATE KEY-----"),
    ),
    "EMAIL": (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),),
    "PHONE": (re.compile(r"\+?\d[\d\s\-()]{7,}\d"),),
    "IP": (
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        re.compile(r"\b(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b"),
    ),
    "ADDRESS": (
        re.compile(r"\b\d+\s+[A-Za-z0-9.\s]+?(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln)\b"),
    ),
    "ORG": (
        re.compile(
            r"\b([A-Z][A-Za-z&]+(?:\s+[A-Z][A-Za-z&]+)*\s+(?:Inc|LLC|Corp|Corporation|Ltd|GmbH|AG|SA|Company|Co))\b"
        ),
    ),
    "PERSON": (
        re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b"),
        re.compile(r"\b[A-Z][a-z]+\b"),
    ),
    "DEVICE": (
        re.compile(r"\b[A-Z]{2,}-\d{1,3}\b"),
        re.compile(r"\bv\d+\.\d+\b"),
        re.compile(r"\bRev\s?[A-Z]\b"),
    ),
}

LIGHT_CATEGORIES = {"SECRET", "EMAIL", "PHONE", "IP", "PERSON"}
HEAVY_EXTRA_CATEGORIES = {"ORG", "ADDRESS", "DEVICE"}

PERSON_STOPWORDS = {
    "Contact",
    "Meet",
    "Email",
    "Call",
    "Review",
    "Discuss",
    "Talk",
    "Idea",
    "Project",
    "Assess",
    "Budget",
    "Check",
}


def _default_whitelists() -> Dict[str, Set[str]]:
    return {
        "PERSON": set(),
        "ORG": set(),
        "ADDRESS": set(),
        "IP": set(),
        "DEVICE": set(),
        "SECRET": set(),
        "EMAIL": set(),
        "PHONE": set(),
    }


@dataclass
class Redactor:
    """Central redactor handling placeholder mapping."""

    global_whitelist: Dict[str, Set[str]] = field(default_factory=_default_whitelists)
    role_whitelist: Dict[str, Set[str]] = field(
        default_factory=lambda: {"Regulatory": {"FAA", "FDA", "ISO", "IEC", "CE"}}
    )
    alias_map: Dict[str, str] = field(default_factory=dict)
    _counters: Dict[str, int] = field(default_factory=dict)

    def _placeholder(self, category: str, value: str) -> str:
        if value in self.alias_map:
            return self.alias_map[value]
        self._counters[category] = self._counters.get(category, 0) + 1
        token = f"[{category}_{self._counters[category]}]"
        self.alias_map[value] = token
        return token

    def redact(
        self, text: str, mode: str = "light", role: Optional[str] = None
    ) -> Tuple[str, Dict[str, str], Set[str]]:
        """Redact *text* according to *mode* and *role*."""

        if not text:
            return text, dict(self.alias_map), set()

        categories = set(LIGHT_CATEGORIES)
        if mode == "heavy":
            categories |= HEAVY_EXTRA_CATEGORIES

        placeholders_seen: Set[str] = set()
        combined_whitelist: Set[str] = set()
        if role and role in self.role_whitelist:
            combined_whitelist.update(self.role_whitelist[role])

        org_terms: Set[str] = set()
        address_terms: Set[str] = set()
        if "ORG" not in categories:
            for pat in PATTERNS.get("ORG", () ):
                for m in pat.finditer(text):
                    org_terms.add(m.group(0))
        if "ADDRESS" not in categories:
            for pat in PATTERNS.get("ADDRESS", () ):
                for m in pat.finditer(text):
                    term = m.group(0)
                    address_terms.add(term)
                    parts = term.split()
                    if parts and parts[0].isdigit():
                        address_terms.add(" ".join(parts[1:]))
        split_terms: Set[str] = set()
        for term in list(org_terms | address_terms):
            split_terms.update(term.split())
        org_terms |= split_terms
        address_terms |= split_terms

        def _replace(match: re.Match[str], category: str) -> str:
            original = match.group(0)
            if PLACEHOLDER_RE.fullmatch(original):
                return original
            if category == "PERSON" and " " in original:
                parts = original.split()
                if parts[0] in PERSON_STOPWORDS and len(parts) == 2:
                    target = parts[1]
                    if target in combined_whitelist or target in self.global_whitelist.get("PERSON", set()):
                        return original
                    token = self._placeholder("PERSON", target)
                    placeholders_seen.add(token)
                    return f"{parts[0]} {token}"
            if category == "PERSON":
                if original in PERSON_STOPWORDS or original in org_terms or original in address_terms:
                    return original
            if original in combined_whitelist or original in self.global_whitelist.get(category, set()):
                return original
            token = self._placeholder(category, original)
            placeholders_seen.add(token)
            return token

        result = text
        for category in [
            "SECRET",
            "EMAIL",
            "PHONE",
            "IP",
            "ADDRESS",
            "ORG",
            "PERSON",
            "DEVICE",
        ]:
            if category not in categories:
                continue
            for pat in PATTERNS.get(category, ()):  # type: ignore[arg-type]
                result = pat.sub(lambda m, c=category: _replace(m, c), result)

        return result, dict(self.alias_map), placeholders_seen

    def note_for_placeholders(self, placeholders: Set[str]) -> str:
        if not placeholders:
            return ""
        sample = ", ".join(sorted(placeholders)[:2])
        return f"Placeholders like {sample} are aliases. Use them verbatim."


def redact_text(text: str, mode: str = "light", role: Optional[str] = None):
    r = Redactor()
    redacted, alias_map, placeholders = r.redact(text, mode=mode, role=role)
    return redacted, alias_map, placeholders


__all__ = ["Redactor", "redact_text"]
