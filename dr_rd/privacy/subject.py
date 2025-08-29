from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Iterable, Optional

import yaml

from .pii import get_pii_patterns

_CFG_PATH = os.path.join("config", "retention.yaml")
_CFG = yaml.safe_load(open(_CFG_PATH)) if os.path.exists(_CFG_PATH) else {}


def _as_json(obj: Any) -> Any:
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except Exception:
            return obj
    return obj


def collect_identifiers(json_or_text: Any) -> Dict[str, Iterable[str]]:
    """Collect identifiers from JSON structure or raw text."""
    data = _as_json(json_or_text)
    text = json.dumps(data) if not isinstance(data, str) else data
    patterns = get_pii_patterns()
    results: Dict[str, list[str]] = {}

    # regex based extraction
    for field, pat in patterns.items():
        found = pat.findall(text)
        if found:
            results[field] = list(set(found))

    # explicit fields from config
    fields = (
        _CFG.get("privacy", {})
        .get("identifiers", {})
        .get("fields", [])
    )

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in fields and isinstance(v, (str, int)):
                    results.setdefault(k, []).append(str(v))
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)
        elif isinstance(obj, str):
            for field, pat in patterns.items():
                for m in pat.findall(obj):
                    results.setdefault(field, []).append(m)

    if isinstance(data, (dict, list)):
        walk(data)

    return results


def derive_subject_key(record_or_text: Any, fields: Iterable[str], salt_env: str) -> Optional[str]:
    """Derive a stable subject key by hashing identifiers with an env salt."""
    identifiers = collect_identifiers(record_or_text)
    parts: list[str] = []
    for f in fields:
        for val in identifiers.get(f, []):
            parts.append(f"{f}:{val}")
    if not parts:
        return None
    salt = os.getenv(salt_env, "")
    if not salt:
        return None
    base = "|".join(sorted(parts))
    return hashlib.sha256((salt + base).encode("utf-8")).hexdigest()
