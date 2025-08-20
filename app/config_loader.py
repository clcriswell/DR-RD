"""Helpers to load mode and pricing configuration and create a CostTracker."""

from pathlib import Path
import os
import yaml
import logging
from core.budget import CostTracker
from config.model_routing import _cheap_default, TEST_MODEL_ID

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_mode(mode: str) -> tuple[dict, CostTracker]:
    modes_path = CONFIG_DIR / "modes.yaml"
    prices_path = Path(os.getenv("PRICES_PATH", CONFIG_DIR / "prices.yaml"))

    with open(modes_path) as fh:
        modes = yaml.safe_load(fh) or {}
    if mode not in modes:
        logging.warning(
            "Requested mode '%s' not found. Falling back to 'test'.", mode
        )
    mode_cfg = modes.get(mode, modes.get("test", {}))
    weights = mode_cfg.get("stage_weights")
    if isinstance(weights, dict):
        total = sum(weights.values())
        if abs(total - 1.0) > 0.05 and total > 0:
            logging.warning(
                "stage_weights for mode %s sum to %.3f; normalizing", mode, total
            )
            mode_cfg["stage_weights"] = {k: v / total for k, v in weights.items()}

    with open(prices_path) as fh:
        prices = yaml.safe_load(fh) or {}

    if mode == "test":
        cheap = TEST_MODEL_ID or _cheap_default(prices.get("models", {}))
        mode_cfg["models"] = {s: cheap for s in ["plan", "exec", "synth"]}

    budget = CostTracker(mode_cfg, prices)
    return mode_cfg, budget
