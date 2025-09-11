# core/redaction.py
from __future__ import annotations
import re
import random
from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, Optional, Iterable

PLACEHOLDER_RE = re.compile(r'^\[(SECRET|EMAIL|PHONE|IPV6|IP|ADDRESS|PERSON|ORG|DEVICE)_\d+\]$')
TOKEN_FINDER_RE = re.compile(r'\[(PERSON|ORG|ADDRESS|IP|DEVICE)_\d+\]')

# Basic patterns (keep conservative)
PATTERNS = {
    "SECRET": re.compile(r'(?:sk-[A-Za-z0-9]{20,}|api[_-]?key\s*=\s*[A-Za-z0-9]{16,})', re.I),
    "EMAIL":  re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    # Require separators to avoid matching short numeric codes
    "PHONE":  re.compile(r'\b(?:(?:\+\d{1,3}[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]\d{3}[-.\s]\d{4})\b'),
    # Strict IPv4 pattern (0-255) to avoid generic dotted numbers
    "IP":     re.compile(r'\b(?:(?:25[0-5]|2[0-4]\d|1?\d{1,2})\.){3}(?:25[0-5]|2[0-4]\d|1?\d{1,2})\b'),
    "IPV6":   re.compile(r'\b(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}\b', re.I),
    "ADDRESS":re.compile(r'\b\d{1,5}\s+[A-Za-z0-9.\s]+\b(?:St|Street|Rd|Road|Ave|Avenue|Blvd|Lane|Ln|Dr|Drive)\b', re.I),
    "PERSON": re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'),  # two+ capitalized words
    "ORG":    re.compile(r'\b([A-Z][A-Za-z0-9&.\-\s]+(?:Inc|LLC|Corp|Corporation|Ltd|GmbH|AG|SA|Company|Co)\.?)\b'),
    "DEVICE": re.compile(r'\b([A-Z]{2,}-\d{2,}|\bv\d+\.\d+\b|Rev\s+[A-Z])\b', re.I),
}

ROLE_NAMES = {
    "Planner",
    "CTO",
    "Regulatory",
    "Finance",
    "Marketing Analyst",
    "IP Analyst",
    "HRM",
    "Materials Engineer",
    "QA",
    "QA Engineer",
    "Quality Assurance",
    "Dynamic Specialist",
    "Synthesizer",
    "Research Scientist",
    "Finance Analyst",
    "Marketing",
    "Chief Scientist",
    "Regulatory Specialist",
    "Evaluation",
    "Simulation",
    "Reflection",
    "Mechanical Systems Lead",
}

INTERNAL_ROLES = {
    "CTO",
    "Materials Engineer",
    "Finance",
    "Regulatory",
    "Marketing Analyst",
    "QA",
    "Research Scientist",
}

DEFAULT_GLOBAL_WHITELIST = {
    "PERSON": {"Alice", "Bob", *ROLE_NAMES},
    "ORG": set(),
    "ADDRESS": set(),
    "IP": set(),
    "DEVICE": set(),
}
DEFAULT_ROLE_WHITELIST = {role: set() for role in ROLE_NAMES}
DEFAULT_ROLE_WHITELIST["Regulatory"].update({"FAA", "FDA", "ISO", "IEC", "CE"})

ROLE_SUFFIXES = {
    "Materials Engineer": ["Scope", "Alloy", "Composite"],
    "Research Scientist": ["Lab", "Analyzer", "Scope"],
    "Dynamic Specialist": ["Module", "Unit"],
    "CTO": ["Core", "System"],
}
LOW_NEED_ROLES = {"QA", "HRM", "IP Analyst"}
GENERIC_ALIASES = ["the product", "the device", "the system"]

@dataclass
class Redactor:
    global_whitelist: Dict[str, Set[str]] = field(default_factory=lambda: {k:set(v) for k,v in DEFAULT_GLOBAL_WHITELIST.items()})
    role_whitelist: Dict[str, Set[str]] = field(default_factory=lambda: {k:set(v) for k,v in DEFAULT_ROLE_WHITELIST.items()})
    alias_map: Dict[str, str] = field(default_factory=dict)
    project_name: Optional[str] = None
    counters: Dict[str, int] = field(
        default_factory=lambda: {
            k: 0
            for k in [
                "SECRET",
                "EMAIL",
                "PHONE",
                "IPV6",
                "IP",
                "ADDRESS",
                "PERSON",
                "ORG",
                "DEVICE",
            ]
        }
    )

    def _is_placeholder(self, s: str) -> bool:
        return bool(PLACEHOLDER_RE.fullmatch(s))

    def _next(self, cat: str) -> str:
        self.counters[cat] += 1
        return f'[{cat}_{self.counters[cat]}]'

    def add_allowed_entities(self, terms: Iterable[str], category: str = "PERSON", role: Optional[str] = None) -> None:
        target = self.role_whitelist.setdefault(role, set()) if role else self.global_whitelist.setdefault(category, set())
        target.update(terms)

    def _allowlisted(self, cat: str, s: str, role: Optional[str]) -> bool:
        s_norm = s.strip().strip(",.()")
        if s_norm in self.global_whitelist.get(cat, set()):
            return True
        if role and s_norm in self.role_whitelist.get(role, set()):
            return True
        return False

    def _replace(self, text: str, cat: str, role: Optional[str], placeholders_seen: Set[str], descriptive: bool) -> str:
        pat = PATTERNS[cat]
        def _sub(m):
            original = m.group(0)
            if self._is_placeholder(original):
                return original
            if cat == "PERSON" and " " in original:
                parts = original.split()
                if parts[0] in {"Contact","Meet","Email","Call"} and len(parts) >= 2:
                    key = " ".join(parts[1:])
                    if self._allowlisted(cat, key, role):
                        return original
                    ph = self.alias_map.get(key)
                    if not ph:
                        if descriptive:
                            base = re.sub(r'\W+', '', key) or cat.title()
                            self.counters[cat] += 1
                            ph = f"{base}X{self.counters[cat]}"
                        else:
                            ph = self._next(cat)
                        self.alias_map[key] = ph
                    placeholders_seen.add(ph)
                    return f"{parts[0]} {ph}"
            # Extract inner for grouped cats (PERSON/ORG/DEVICE) if defined
            key = m.group(1) if (cat in {"PERSON","ORG","DEVICE"} and m.lastindex) else original
            if self._allowlisted(cat, key, role):
                return original
            if cat == "PERSON" and re.search(r"\b(Inc|LLC|Corp|Corporation|Ltd|Company|Co|St|Street|Rd|Road|Ave|Avenue|Blvd|Lane|Ln|Dr|Drive)\b", key):
                return original
            if key in self.alias_map:
                ph = self.alias_map[key]
            else:
                if descriptive and cat in {"PERSON","ORG","DEVICE"}:
                    base = re.sub(r'\W+', '', key) or cat.title()
                    self.counters[cat] += 1
                    ph = f"{base}X{self.counters[cat]}"
                else:
                    ph = self._next(cat)
                self.alias_map[key] = ph
            placeholders_seen.add(ph)
            return ph
        return pat.sub(_sub, text)

    def redact(
        self,
        text: str,
        mode: str = "light",
        role: Optional[str] = None,
        categories: Optional[Iterable[str]] = None,
    ) -> Tuple[str, Dict[str, str], Set[str]]:
        if not text:
            return text, self.alias_map, set()
        placeholders_seen: Set[str] = set()

        if self.project_name and role:
            if role in LOW_NEED_ROLES:
                alias = random.choice(GENERIC_ALIASES)
            else:
                base = self.project_name.title()
                base = re.sub(r'^(?:A |An |The )', '', base)
                base = re.sub(r"[^0-9A-Za-z]+", "", base) or "Project"
                suffix = random.choice(ROLE_SUFFIXES.get(role, ["Device"]))
                m = re.match(r"[A-Za-z]+", suffix)
                prefix = m.group(0) if m else ""
                if base.lower().endswith("device") and prefix.lower() != "device":
                    base = base[: -len("Device")]
                if prefix and base.lower().endswith(prefix.lower()):
                    alias = f"{base}{suffix[m.end():]}"
                else:
                    alias = f"{base}{suffix}"
            text = re.sub(re.escape(self.project_name), alias, text, flags=re.I)
            self.alias_map[self.project_name] = alias

        if categories is not None:
            order = list(categories)
        else:
            order = ["SECRET", "EMAIL", "PHONE", "IP", "IPV6"]
            if mode == "heavy":
                order += ["PERSON", "ORG", "ADDRESS", "DEVICE"]
            elif mode == "logging":
                order = ["SECRET", "EMAIL", "PHONE"]
            else:  # light
                order += ["PERSON"]  # minimally alias people

        if role in INTERNAL_ROLES:
            order = ["SECRET", "EMAIL", "PHONE"]

        out = text
        descriptive = mode != "heavy"
        for cat in order:
            out = self._replace(out, cat, role, placeholders_seen, descriptive)
        return out, dict(self.alias_map), placeholders_seen

    @staticmethod
    def note_for_placeholders(placeholders_seen: Iterable[str]) -> str:
        return "Placeholders like [PERSON_1] or AliceX1 are aliases. Use them verbatim."

def redact_text(text: str, mode: str = "light", role: Optional[str] = None):
    r = Redactor()
    return r.redact(text, mode=mode, role=role)
