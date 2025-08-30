from __future__ import annotations

from typing import Dict, Optional, Tuple

from .secrets import get as secret_get
from .pricing import get as price_get, table as price_table
from .prefs import load_prefs

REGISTRY: Dict[str, Dict] = {
    "openai": {
        "env_keys": ["OPENAI_API_KEY"],
        "models": {"gpt-4o-mini": {}, "gpt-4o": {}},
        "default_by_mode": {"standard": "gpt-4o-mini", "demo": "gpt-4o-mini"},
    },
    "anthropic": {
        "env_keys": ["ANTHROPIC_API_KEY"],
        "models": {"claude-3-5-sonnet": {}},
        "default_by_mode": {"standard": "claude-3-5-sonnet"},
    },
}


def available_providers() -> Dict[str, Dict]:
    return REGISTRY


def has_secrets(provider: str) -> bool:
    info = REGISTRY.get(provider, {})
    keys = info.get("env_keys", [])
    for k in keys:
        if not secret_get(k):
            return False
    return True


def list_models(provider: str) -> Dict[str, Dict]:
    return REGISTRY.get(provider, {}).get("models", {})


def model_key(provider: str, model: str) -> str:
    return f"{provider}:{model}"


def model_price(provider: str, model: str) -> Dict[str, float]:
    return price_get(model_key(provider, model))


def default_model_for_mode(mode: str) -> Tuple[str, str]:
    for prov, info in REGISTRY.items():
        default = info.get("default_by_mode", {}).get(mode)
        if default:
            return prov, default
    # fallback to first provider/model
    prov = next(iter(REGISTRY.keys()))
    mdl = next(iter(REGISTRY[prov]["models"].keys()))
    return prov, mdl


def from_prefs_snapshot(s: Dict) -> Optional[Tuple[str, str]]:
    if not isinstance(s, dict):
        return None
    prov = s.get("provider")
    mdl = s.get("model")
    if prov in REGISTRY and mdl in REGISTRY[prov]["models"]:
        return prov, mdl
    return None


def to_prefs_snapshot(provider: str, model: str) -> Dict:
    if provider not in REGISTRY or model not in REGISTRY[provider]["models"]:
        raise KeyError("unknown provider/model")
    return {"provider": provider, "model": model}


def get_active_model(mode: str, override: Optional[Tuple[str, str]] = None) -> Tuple[str, str]:
    if override:
        return override
    prefs = load_prefs()
    snap = prefs.get("defaults", {}).get("provider_model")
    sel = from_prefs_snapshot(snap) if isinstance(snap, dict) else None
    if sel:
        return sel
    return default_model_for_mode(mode)


def pricing_table() -> Dict[str, Dict[str, float]]:
    return price_table()

