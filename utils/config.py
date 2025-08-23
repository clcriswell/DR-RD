from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml


def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _coerce(value: str) -> Any:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def load_config(overrides_path: str | None = None) -> Dict[str, Any]:
    base_path = Path(__file__).resolve().parent.parent / "config" / "defaults.yaml"
    with open(base_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    override_file = overrides_path or (
        Path("config/local.yaml") if Path("config/local.yaml").exists() else None
    )
    if override_file and Path(override_file).exists():
        with open(override_file, "r", encoding="utf-8") as f:
            override = yaml.safe_load(f) or {}
        cfg = _deep_merge(cfg, override)
    prefix = "APP__"
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix) :].lower().split("__")
        d = cfg
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = _coerce(value)
    return cfg
