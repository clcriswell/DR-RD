from __future__ import annotations

from pathlib import Path
from typing import Dict
import yaml

PRICING_PATH = Path('pricing.yaml')

DEFAULTS: Dict[str, Dict[str, float]] = {
    "openai:gpt-4o-mini": {"input_per_1k": 0.15, "output_per_1k": 0.60},
    "openai:gpt-4o": {"input_per_1k": 5.00, "output_per_1k": 15.00},
    "anthropic:claude-3-5-sonnet": {"input_per_1k": 3.00, "output_per_1k": 15.00},
}

_cache: Dict[str, Dict[str, float]] | None = None

def _load() -> Dict[str, Dict[str, float]]:
    global _cache
    if _cache is not None:
        return _cache
    data = dict(DEFAULTS)
    if PRICING_PATH.exists():
        try:
            with PRICING_PATH.open('r', encoding='utf-8') as fh:
                extra = yaml.safe_load(fh) or {}
            if isinstance(extra, dict):
                for k, v in extra.items():
                    try:
                        inp = float(v.get('input_per_1k'))
                        out = float(v.get('output_per_1k'))
                        data[k] = {"input_per_1k": inp, "output_per_1k": out}
                    except Exception:
                        continue
        except Exception:
            pass
    _cache = data
    return data


def table() -> Dict[str, Dict[str, float]]:
    """Return mapping of model_key -> pricing info."""
    return dict(_load())


def get(model_key: str) -> Dict[str, float]:
    """Return pricing for ``model_key`` or empty dict if unknown."""
    return dict(_load().get(model_key, {}))

