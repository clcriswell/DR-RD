from __future__ import annotations
from pathlib import Path
import json, threading
from typing import Any, Dict

_LOCALE_DIR = Path("locales")
_DEFAULT = "en"
_cache: dict[str, dict[str, str]] = {}
_lock = threading.Lock()


def _load(lang: str) -> dict[str, str]:
    p = _LOCALE_DIR / f"{lang}.json"
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def set_locale(lang: str) -> None:
    # store in a tiny state file for non UI consumers
    state_dir = Path(".dr_rd")
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "lang.json").write_text(json.dumps({"lang": lang}), encoding="utf-8")


def get_locale(default: str = _DEFAULT) -> str:
    try:
        j = json.loads((Path(".dr_rd") / "lang.json").read_text(encoding="utf-8"))
        return j.get("lang") or default
    except Exception:
        return default


def tr(key: str, *, lang: str | None = None, **fmt: Any) -> str:
    lang = lang or get_locale()
    with _lock:
        if lang not in _cache:
            _cache[lang] = _load(lang)
        if _DEFAULT not in _cache:
            _cache[_DEFAULT] = _load(_DEFAULT)
    s = _cache[lang].get(key) or _cache[_DEFAULT].get(key) or key
    try:
        return s.format(**fmt) if fmt else s
    except Exception:
        return s


def missing_keys(lang: str) -> list[str]:
    with _lock:
        loc = _cache.get(lang) or _load(lang)
        base = _cache.get(_DEFAULT) or _load(_DEFAULT)
    return [k for k in base.keys() if k not in loc]


__all__ = ["tr", "set_locale", "get_locale", "missing_keys"]
