from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml

from dr_rd.safety.filters import PII_PATTERNS as SAFETY_PATTERNS

_CFG_PATH = Path("config/retention.yaml")
_CFG = yaml.safe_load(_CFG_PATH.read_text()) if _CFG_PATH.exists() else {}

_DEFAULT_PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I),
    "phone": re.compile(r"\+?\d[\d\-\s]{7,}\d"),
    "ip": re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
    "gov_id": re.compile(r"\b[A-Z0-9]{8,}\b", re.I),
    "api_keys": re.compile(r"\b[a-zA-Z0-9]{20,}\b"),
}


def get_pii_patterns() -> Dict[str, re.Pattern]:
    cfg = _CFG.get("privacy", {}).get("pii_detection", {})
    pats: Dict[str, re.Pattern] = {}
    for name, enabled in cfg.items():
        if name == "custom_patterns" and isinstance(enabled, list):
            for i, pat in enumerate(enabled):
                pats[f"custom_{i}"] = re.compile(pat, re.I)
        elif enabled:
            pats[name] = SAFETY_PATTERNS.get(name) or _DEFAULT_PATTERNS.get(name)
    return pats


def redact_text(text: str, redaction_token: str) -> str:
    for pat in get_pii_patterns().values():
        text = pat.sub(redaction_token, text)
    return text


def redact_json(obj: Any, redaction_token: str) -> Any:
    if isinstance(obj, dict):
        return {k: redact_json(v, redaction_token) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_json(v, redaction_token) for v in obj]
    if isinstance(obj, str):
        return redact_text(obj, redaction_token)
    return obj
