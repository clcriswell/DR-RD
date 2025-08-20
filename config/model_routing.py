from dataclasses import dataclass
import os
from pathlib import Path
import yaml

DEFAULTS = {
    "PLANNER": "gpt-5",
    "RESEARCHER": "gpt-5",
    "EVALUATOR": "gpt-5",
    "SYNTHESIZER": "gpt-5",
    "FINAL_SYNTH": "gpt-5",
    "BRAIN_MODE_LOOP": "gpt-5",
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
TEST_MODEL_ID = os.getenv("TEST_MODEL_ID", None)


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
    prices = prices or PRICE_TABLE
    if mode == "test":
        return TEST_MODEL_ID or _cheap_default(prices)
    key = (role or stage or "").upper()
    return DEFAULTS.get(key, DEFAULTS.get(stage.upper(), "gpt-5"))
