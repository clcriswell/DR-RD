"""Helpers to load mode and pricing configuration and create a BudgetManager."""

from pathlib import Path
import os
import yaml
import logging
from core.budget import BudgetManager

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_mode(mode: str) -> tuple[dict, BudgetManager]:
    modes_path = CONFIG_DIR / "modes.yaml"
    prices_path = Path(os.getenv("PRICES_PATH", CONFIG_DIR / "prices.yaml"))

    with open(modes_path) as fh:
        modes = yaml.safe_load(fh) or {}
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

    budget = BudgetManager(mode_cfg, prices)
    return mode_cfg, budget
