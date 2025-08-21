from __future__ import annotations

import re
from collections import OrderedDict
from typing import Any, Dict, Tuple, Union

try:
    import spacy  # type: ignore

    try:
        _NLP = spacy.load("en_core_web_sm")
    except Exception:  # pragma: no cover - model may be missing
        _NLP = None
except Exception:  # pragma: no cover - spaCy not installed
    spacy = None
    _NLP = None


def generate_alias_map(text: str) -> OrderedDict[str, str]:
    """Return an OrderedDict mapping detected entities to aliases."""
    candidates: list[tuple[int, str, str]] = []
    if _NLP:
        doc = _NLP(text)
        for ent in doc.ents:
            if ent.label_ in {"PERSON", "ORG", "PRODUCT"}:
                candidates.append((ent.start_char, ent.text, ent.label_))
    patterns = [
        (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "EMAIL"),
        (r"\+?\d[\d\s\-]{7,}\d", "PHONE"),
    ]
    for pat, ttype in patterns:
        for m in re.finditer(pat, text):
            candidates.append((m.start(), m.group(0), ttype))
    if not _NLP:
        for m in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", text):
            val = m.group(1)
            token = val.split()[-1]
            ttype = "ORG" if token in {"Corp", "Inc", "LLC", "Company"} else "PERSON"
            candidates.append((m.start(), val, ttype))
    candidates.sort(key=lambda x: x[0])
    aliases: OrderedDict[str, str] = OrderedDict()
    counters: Dict[str, int] = {}
    for _, value, ttype in candidates:
        if value in aliases:
            continue
        counters[ttype] = counters.get(ttype, 0) + 1
        aliases[value] = f"[{ttype}_{counters[ttype]}]"
    return aliases


def _apply_aliases(obj: Any, mapping: Dict[str, str]) -> Any:
    items = sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True)
    if isinstance(obj, str):
        out = obj
        for orig, alias in items:
            out = out.replace(orig, alias)
        return out
    if isinstance(obj, list):
        return [_apply_aliases(v, mapping) for v in obj]
    if isinstance(obj, dict):
        return {k: _apply_aliases(v, mapping) for k, v in obj.items()}
    return obj


def _gather_text(obj: Union[dict, list, str]) -> str:
    parts: list[str] = []

    def _g(o: Any) -> None:
        if isinstance(o, str):
            parts.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                _g(v)
        elif isinstance(o, list):
            for v in o:
                _g(v)

    _g(obj)
    return " ".join(parts)


def pseudonymize_for_model(
    payload: Union[dict, str],
) -> Tuple[Union[dict, str], OrderedDict[str, str]]:
    text = _gather_text(payload)
    alias_map = generate_alias_map(text)
    pseudo = _apply_aliases(payload, alias_map)
    return pseudo, alias_map


def rehydrate_output(obj: Union[dict, str], alias_map: Dict[str, str]) -> Union[dict, str]:
    reverse = {v: k for k, v in alias_map.items()}
    return _apply_aliases(obj, reverse)


ALLOWLIST = {
    "CTO",
    "Planner",
    "Research Scientist",
    "Regulatory",
    "Synthesizer",
    "Finance",
    "IP Analyst",
    "Marketing Analyst",
    "Mechanical Systems Lead",
    "Project Manager",
    "Risk Manager",
}


def redact_for_logging(obj: Union[dict, str]) -> Union[dict, str]:
    text = _gather_text(obj)
    alias_map = generate_alias_map(text)
    filtered = {orig: alias for orig, alias in alias_map.items() if orig not in ALLOWLIST}
    redactions = {orig: alias.replace("[", "[REDACTED:") for orig, alias in filtered.items()}
    return _apply_aliases(obj, redactions)


__all__ = [
    "generate_alias_map",
    "pseudonymize_for_model",
    "rehydrate_output",
    "redact_for_logging",
]
