"""Helpers for persisted user preferences."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .clients import get_firestore_client

CONFIG_DIR = Path(".dr_rd")
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_PREFS: dict[str, Any] = {
    "version": 1,
    "defaults": {
        "mode": "standard",
        "budget_limit_usd": None,
        "max_tokens": None,
        "knowledge_sources": ["samples"],
    },
    "ui": {
        "show_trace_by_default": True,
        "auto_export_on_completion": False,
        "trace_page_size": 50,
    },
    "privacy": {
        "telemetry_enabled": True,
        "include_advanced_in_share_links": False,
    },
}

_ALLOWED_SECTIONS = {"defaults", "ui", "privacy", "version"}


def _validate(raw: Mapping[str, Any] | None) -> dict:
    """Return a sanitized preferences dict."""
    prefs = json.loads(json.dumps(DEFAULT_PREFS))  # deep copy
    if not isinstance(raw, Mapping):
        return prefs

    if isinstance(raw.get("version"), int):
        prefs["version"] = raw["version"]

    def _coerce(section: str, key: str, value: Any) -> None:
        base = DEFAULT_PREFS[section][key]
        if isinstance(base, bool):
            prefs[section][key] = bool(value)
        elif isinstance(base, int):
            try:
                prefs[section][key] = int(value)
            except Exception:
                pass
        elif isinstance(base, float) or base is None:
            if value is None:
                prefs[section][key] = None
            else:
                try:
                    if key.endswith("tokens"):
                        prefs[section][key] = int(value)
                    else:
                        prefs[section][key] = float(value)
                except Exception:
                    pass
        elif isinstance(base, list):
            if isinstance(value, list):
                prefs[section][key] = [str(v) for v in value]
        else:
            prefs[section][key] = str(value)

    for section in ("defaults", "ui", "privacy"):
        raw_section = raw.get(section)
        if not isinstance(raw_section, Mapping):
            continue
        for key, value in raw_section.items():
            if key not in prefs[section]:
                continue
            _coerce(section, key, value)

    # Clamp trace_page_size
    tps = prefs["ui"]["trace_page_size"]
    try:
        tps = int(tps)
    except Exception:
        tps = DEFAULT_PREFS["ui"]["trace_page_size"]
    prefs["ui"]["trace_page_size"] = max(10, min(200, tps))
    return prefs


def load_prefs() -> dict:
    """Load preferences from disk, creating defaults if missing."""
    if not CONFIG_PATH.exists():
        save_prefs(DEFAULT_PREFS)
        return json.loads(json.dumps(DEFAULT_PREFS))
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    return _validate(data)


def mirror_to_firestore(prefs: Mapping[str, Any]) -> None:
    """Best effort mirror to Firestore; ignore failures."""
    try:
        client = get_firestore_client()
        if not client:
            return
        client.collection("prefs").document("config").set(dict(prefs))
    except Exception:
        pass


def save_prefs(prefs: Mapping[str, Any]) -> None:
    """Validate and atomically write preferences."""
    data = _validate(prefs)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(CONFIG_PATH)
    mirror_to_firestore(data)


def merge_defaults(run_defaults: dict) -> dict:
    """Overlay stored default run values onto ``run_defaults``."""
    prefs = load_prefs()
    merged = dict(run_defaults)
    for k, v in prefs.get("defaults", {}).items():
        if k in merged:
            merged[k] = v
    return merged


def get_flag(path: str, default: Any = None) -> Any:
    """Retrieve a nested flag using dot notation."""
    prefs = load_prefs()
    cur: Any = prefs
    for part in path.split("."):
        if isinstance(cur, Mapping) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def set_flag(path: str, value: Any) -> dict:
    """Set a nested flag without writing to disk."""
    prefs = load_prefs()
    cur: Any = prefs
    parts = path.split(".")
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            return prefs
        cur = nxt
    cur[parts[-1]] = value
    return _validate(prefs)


__all__ = [
    "CONFIG_DIR",
    "CONFIG_PATH",
    "DEFAULT_PREFS",
    "load_prefs",
    "save_prefs",
    "merge_defaults",
    "get_flag",
    "set_flag",
]
