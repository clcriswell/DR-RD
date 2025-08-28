from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

import yaml

from dr_rd.cache.file_cache import FileCache

_ROOT = Path(__file__).resolve().parents[2]
_CFG_PATH = _ROOT / "config" / "models.yaml"

_cache = FileCache()
_cfg: Dict[str, Any] | None = None


def _load_cfg() -> Dict[str, Any]:
    global _cfg
    if _cfg is None:
        with open(_CFG_PATH, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        _cfg = data.get("caching", {})
    return _cfg


def prompt_hash(prompt_obj: Dict[str, Any]) -> str:
    keys = {k: prompt_obj.get(k) for k in ["system", "user", "few_shots", "io_schema_ref", "provider_hints"]}
    payload = json.dumps(keys, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get(phash: str, provider_model: str) -> Any | None:
    cfg = _load_cfg()
    if not cfg.get("enabled", False):
        return None
    ttl = int(cfg.get("ttl_s", 0))
    return _cache.get(f"{provider_model}:{phash}", ttl)


def put(phash: str, provider_model: str, value: Any) -> None:
    cfg = _load_cfg()
    if not cfg.get("enabled", False):
        return
    _cache.set(f"{provider_model}:{phash}", value)


__all__ = ["prompt_hash", "get", "put"]
