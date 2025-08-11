"""Helpers to load mode and pricing configuration and create a BudgetManager."""

from pathlib import Path
import os
import yaml
from core.budget import BudgetManager

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_mode(mode: str) -> tuple[dict, BudgetManager]:
    modes_path = CONFIG_DIR / "modes.yaml"
    prices_path = Path(os.getenv("PRICES_PATH", CONFIG_DIR / "prices.yaml"))

    with open(modes_path) as fh:
        modes = yaml.safe_load(fh) or {}
    mode_cfg = modes.get(mode, modes.get("test", {}))

    with open(prices_path) as fh:
        prices = yaml.safe_load(fh) or {}

    budget = BudgetManager(mode_cfg, prices)
    return mode_cfg, budget
