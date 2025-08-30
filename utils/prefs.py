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
        "provider_model": {"provider": "openai", "model": "gpt-4o-mini"},
        "profile": "",
    },
    "ui": {
        "show_trace_by_default": True,
        "auto_export_on_completion": False,
        "trace_page_size": 50,
        "language": "en",
    },
    "privacy": {
        "telemetry_enabled": True,
        "include_advanced_in_share_links": False,
        "retention_days_events": 30,
        "retention_days_runs": 60,
        "safety_mode": "warn",
        "safety_use_llm": False,
        "safety_block_categories": ["exfil", "malicious_instruction"],
        "safety_high_threshold": 0.8,
    },
    "notifications": {
        "enabled": True,
        "channels": [],
        "email_to": [],
        "slack_mention": "",
        "events": {
            "run_completed": True,
            "run_failed": True,
            "run_cancelled": True,
            "timeout": True,
            "budget_exceeded": True,
            "safety_blocked": True,
        },
    },
    "storage": {"backend": "local", "bucket": "", "prefix": "dr_rd", "signed_url_ttl_sec": 600},
    "retrieval": {
        "enabled": True,
        "top_k": 4,
        "chunk_size": 800,
        "chunk_overlap": 120,
        "use_embeddings": True,
        "embedding_provider": "openai",
        "embedding_model": "text-embedding-3-small",
        "max_chars_per_doc": 200000,
    },
    "sharing": {
        "default_ttl_sec": 604800,
        "default_scopes": ["trace", "reports", "artifacts"],
        "allow_scopes": ["trace", "reports", "artifacts"],
    },
}

_ALLOWED_SECTIONS = {
    "defaults",
    "ui",
    "privacy",
    "notifications",
    "storage",
    "retrieval",
    "sharing",
    "version",
}


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

    raw_not = raw.get("notifications")
    if isinstance(raw_not, Mapping):
        np = prefs["notifications"]
        np["enabled"] = bool(raw_not.get("enabled", True))
        chans = []
        for c in raw_not.get("channels", []):
            if isinstance(c, str) and c in {"slack", "email", "webhook"} and c not in chans:
                chans.append(c)
        np["channels"] = chans
        emails = []
        for addr in raw_not.get("email_to", []):
            if isinstance(addr, str):
                emails.append(addr)
            if len(emails) >= 10:
                break
        np["email_to"] = emails
        if isinstance(raw_not.get("slack_mention"), str):
            np["slack_mention"] = raw_not["slack_mention"]
        events = {}
        raw_ev = raw_not.get("events", {})
        for k, v in np["events"].items():
            events[k] = bool(raw_ev.get(k, v))
        np["events"] = events
    for section in ("defaults", "ui", "privacy", "retrieval", "sharing"):
        raw_section = raw.get(section)
        if not isinstance(raw_section, Mapping):
            continue
        for key, value in raw_section.items():
            if key not in prefs[section]:
                continue
            _coerce(section, key, value)
        if section == "sharing":
            allowed = set(DEFAULT_PREFS["sharing"]["allow_scopes"])
            scopes = [s for s in prefs["sharing"]["allow_scopes"] if s in allowed]
            prefs["sharing"]["allow_scopes"] = scopes
            def_scopes = [s for s in prefs["sharing"]["default_scopes"] if s in scopes]
            prefs["sharing"]["default_scopes"] = def_scopes
            try:
                ttl = int(prefs["sharing"]["default_ttl_sec"])
            except Exception:
                ttl = DEFAULT_PREFS["sharing"]["default_ttl_sec"]
            prefs["sharing"]["default_ttl_sec"] = max(60, ttl)

    # Clamp safety threshold
    thr = prefs["privacy"].get("safety_high_threshold", 0.8)
    try:
        thr = float(thr)
    except Exception:
        thr = 0.8
    prefs["privacy"]["safety_high_threshold"] = max(0.0, min(1.0, thr))

    # Clamp retention windows
    for key in ("retention_days_events", "retention_days_runs"):
        days = prefs["privacy"].get(key, DEFAULT_PREFS["privacy"][key])
        try:
            days = int(days)
        except Exception:
            days = DEFAULT_PREFS["privacy"][key]
        prefs["privacy"][key] = max(7, min(365, days))

    # Validate provider/model snapshot
    try:
        from . import providers as _providers

        snap = raw.get("defaults", {}).get("provider_model") if isinstance(raw, Mapping) else None
        sel = _providers.from_prefs_snapshot(snap) if snap else None
        if sel:
            prefs["defaults"]["provider_model"] = _providers.to_prefs_snapshot(*sel)
    except Exception:
        pass

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
