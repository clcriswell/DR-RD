# core/redaction.py
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, Optional, Iterable

PLACEHOLDER_RE = re.compile(r'^\[(SECRET|EMAIL|PHONE|IPV6|IP|ADDRESS|PERSON|ORG|DEVICE)_\d+\]$')
TOKEN_FINDER_RE = re.compile(r'\[(PERSON|ORG|ADDRESS|IP|DEVICE)_\d+\]')

# Basic patterns (keep conservative)
PATTERNS = {
    "SECRET": re.compile(r'(?:sk-[A-Za-z0-9]{20,}|api[_-]?key\s*=\s*[A-Za-z0-9]{16,})', re.I),
    "EMAIL":  re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    "PHONE":  re.compile(r'(?:(?:\+\d{1,3}\s*)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4})'),
    "IP":     re.compile(r'\b(?:(?:\d{1,3}\.){3}\d{1,3})\b'),
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
    "Dynamic Specialist",
    "Synthesizer",
    "Research Scientist",
    "Chief Scientist",
    "Regulatory Specialist",
    "Evaluation",
    "Finance Specialist",
    "Simulation",
    "Materials",
    "Reflection",
    "Mechanical Systems Lead",
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

@dataclass
class Redactor:
    global_whitelist: Dict[str, Set[str]] = field(default_factory=lambda: {k:set(v) for k,v in DEFAULT_GLOBAL_WHITELIST.items()})
    role_whitelist: Dict[str, Set[str]] = field(default_factory=lambda: {k:set(v) for k,v in DEFAULT_ROLE_WHITELIST.items()})
    alias_map: Dict[str, str] = field(default_factory=dict)
    counters: Dict[str, int] = field(default_factory=lambda: {k:0 for k in ["SECRET","EMAIL","PHONE","IPV6","IP","ADDRESS","PERSON","ORG","DEVICE"]})

    def _is_placeholder(self, s: str) -> bool:
        return bool(PLACEHOLDER_RE.fullmatch(s))

    def _next(self, cat: str) -> str:
        self.counters[cat] += 1
        return f'[{cat}_{self.counters[cat]}]'

    def _allowlisted(self, cat: str, s: str, role: Optional[str]) -> bool:
        s_norm = s.strip().strip(",.()")
        if s_norm in self.global_whitelist.get(cat, set()):
            return True
        if role and s_norm in self.role_whitelist.get(role, set()):
            return True
        return False

    def _replace(self, text: str, cat: str, role: Optional[str], placeholders_seen: Set[str]) -> str:
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
                        ph = self._next(cat)
                        self.alias_map[key] = ph
                    placeholders_seen.add(ph)
                    return f"{parts[0]} {ph}"
            # Extract inner for grouped cats (PERSON/ORG/DEVICE) if defined
            key = m.group(1) if (cat in {"PERSON","ORG","DEVICE"} and m.lastindex) else original
            if self._allowlisted(cat, key, role):
                return original
            if key in self.alias_map:
                ph = self.alias_map[key]
            else:
                ph = self._next(cat)
                self.alias_map[key] = ph
            placeholders_seen.add(ph)
            return ph
        return pat.sub(_sub, text)

    def redact(self, text: str, mode: str = "light", role: Optional[str] = None) -> Tuple[str, Dict[str,str], Set[str]]:
        if not text:
            return text, self.alias_map, set()
        placeholders_seen: Set[str] = set()
        # Order matters; secrets first
        order = ["SECRET","EMAIL","PHONE","IP","IPV6"]
        if mode == "heavy":
            order += ["PERSON","ORG","ADDRESS","DEVICE"]
        else:  # light
            order += ["PERSON"]  # minimally alias people
        out = text
        for cat in order:
            out = self._replace(out, cat, role, placeholders_seen)
        return out, dict(self.alias_map), placeholders_seen

    @staticmethod
    def note_for_placeholders(placeholders_seen: Iterable[str]) -> str:
        return "Placeholders like [PERSON_1], [ORG_1] are aliases. Use them verbatim."

def redact_text(text: str, mode: str = "light", role: Optional[str] = None):
    r = Redactor()
    return r.redact(text, mode=mode, role=role)
