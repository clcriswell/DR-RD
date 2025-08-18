from __future__ import annotations

from pathlib import Path
import os
import yaml
from functools import lru_cache

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@lru_cache(maxsize=1)
def load_prices() -> dict:
    path = Path(os.getenv("PRICES_PATH", _CONFIG_DIR / "prices.yaml"))
    try:
        with open(path) as fh:
            data = yaml.safe_load(fh) or {}
    except Exception:
        data = {}
    return data.get("models", {})


def cost_usd(model: str, prompt_toks: int, completion_toks: int) -> float:
    prices = load_prices()
    p = prices.get(model) or prices.get("default", {})
    return (prompt_toks / 1000.0) * p.get("in_per_1k", 0.0) + (
        completion_toks / 1000.0
    ) * p.get("out_per_1k", 0.0)
