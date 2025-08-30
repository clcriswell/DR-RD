from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(".dr_rd/profiles")
ROOT.mkdir(parents=True, exist_ok=True)
SAFE = re.compile(r"[^a-z0-9._-]+")


@dataclass(frozen=True)
class Profile:
    name: str
    path: Path
    data: dict[str, Any]


def _safe_name(name: str) -> str:
    return SAFE.sub("-", name.strip().lower())[:64] or "profile"


def _now() -> float:
    return time.time()


def list_profiles() -> list[Profile]:
    out = []
    for p in ROOT.glob("*.json"):
        try:
            out.append(Profile(p.stem, p, json.loads(p.read_text(encoding="utf-8"))))
        except Exception:
            continue
    return sorted(out, key=lambda pr: pr.data.get("updated_at", 0), reverse=True)


def load(name: str) -> dict[str, Any]:
    p = ROOT / f"{_safe_name(name)}.json"
    obj = json.loads(p.read_text(encoding="utf-8"))
    return _validate(obj)


def save(name: str, defaults: dict[str, Any], description: str = "") -> dict[str, Any]:
    nm = _safe_name(name)
    p = ROOT / f"{nm}.json"
    obj = {
        "version": 1,
        "name": nm,
        "description": description or "",
        "created_at": _now(),
        "updated_at": _now(),
        "defaults": _filter_defaults(defaults),
    }
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return obj


def update(name: str, updates: dict[str, Any]) -> dict[str, Any]:
    p = ROOT / f"{_safe_name(name)}.json"
    obj = json.loads(p.read_text(encoding="utf-8"))
    obj["defaults"] = _filter_defaults({**obj.get("defaults", {}), **updates})
    obj["updated_at"] = _now()
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return obj


def delete(name: str) -> bool:
    p = ROOT / f"{_safe_name(name)}.json"
    if p.exists():
        p.unlink()
        return True
    return False


def _filter_defaults(d: dict[str, Any]) -> dict[str, Any]:
    allow = {
        "mode",
        "provider_model",
        "budget_limit_usd",
        "max_tokens",
        "knowledge_sources",
        "retrieval",
        "safety",
        "flags",
    }
    out = {k: d[k] for k in list(d.keys()) if k in allow}
    # clamp and sanitize
    if "budget_limit_usd" in out:
        out["budget_limit_usd"] = max(0.0, float(out["budget_limit_usd"]))
    if "max_tokens" in out:
        out["max_tokens"] = max(1, int(out["max_tokens"]))
    if "knowledge_sources" in out and not isinstance(out["knowledge_sources"], list):
        out["knowledge_sources"] = []
    return out


def _validate(obj: dict[str, Any]) -> dict[str, Any]:
    assert int(obj.get("version", 1)) == 1
    assert "defaults" in obj
    _filter_defaults(obj["defaults"])  # normalize
    return obj


def apply_to_config(config: dict[str, Any], prof: dict[str, Any]) -> dict[str, Any]:
    d = {**config}
    defaults = prof.get("defaults", {})
    for k, v in defaults.items():
        if d.get(k) in (None, "", [], {}):
            d[k] = v
    return d
