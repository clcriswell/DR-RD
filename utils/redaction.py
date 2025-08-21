from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Dict, Any
import yaml


def load_policy(path_or_dict: Any) -> Dict[str, Any]:
    if isinstance(path_or_dict, dict):
        return path_or_dict
    path = Path(path_or_dict)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def redact_text(text: str, *, policy: Dict[str, Any]) -> str:
    if not text:
        return text
    result = text
    for name, cfg in policy.items():
        if not cfg.get("enabled", True):
            continue
        pattern = cfg.get("pattern")
        token = cfg.get("token", f"[REDACTED:{name.upper()}]")
        if not pattern:
            continue
        result = re.sub(pattern, token, result, flags=re.IGNORECASE)
    return result
