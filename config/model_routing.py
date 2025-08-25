from dataclasses import dataclass
import logging
import os
from pathlib import Path
import yaml

DEFAULTS = {
    "PLANNER": "gpt-4o-mini",
    "RESEARCHER": "gpt-4o-mini",
    "EVALUATOR": "gpt-4o-mini",
    "SYNTHESIZER": "gpt-4o-mini",
    "FINAL_SYNTH": "gpt-4o-mini",
    "BRAIN_MODE_LOOP": "gpt-4o-mini",
}

def _load_prices() -> dict:
    path = Path(os.getenv("PRICES_PATH", Path(__file__).resolve().parent / "prices.yaml"))
    try:
        with open(path) as fh:
            data = yaml.safe_load(fh) or {}
    except Exception:
        data = {}
    return data.get("models", {})


PRICE_TABLE = _load_prices()


def _cheap_default(prices: dict) -> str:
    def _cost(p):
        if isinstance(p, dict):
            inp = p.get("input", p.get("in_per_1k", 0))
            out = p.get("output", p.get("out_per_1k", 0))
            return float(inp) + float(out)
        return float(p)

    return min(prices, key=lambda k: _cost(prices[k])) if prices else "gpt-5"


@dataclass
class CallHints:
    stage: str  # "plan"|"exec"|"eval"|"synth"|"brain"
    difficulty: str = "normal"  # "easy"|"normal"|"hard"
    deep_reasoning: bool = False
    final_pass: bool = False


def pick_model(stage: str, role: str | None, mode: str, prices: dict | None = None) -> str:
    if mode:
        logging.warning(
            "config.model_routing.pick_model: 'mode' argument is deprecated and ignored; using unified 'standard' routing"
        )
    if role:
        model = DEFAULTS.get(role.upper())
        if model:
            return model
    model = DEFAULTS.get(stage.upper())
    if model:
        return model
    return DEFAULTS.get("RESEARCHER", "gpt-5")


def pick_model_for_stage(stage: str, role: str | None = None, prices: dict | None = None) -> str:
    return pick_model(stage, role, mode="", prices=prices)
