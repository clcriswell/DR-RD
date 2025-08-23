"""Helpers to load mode and pricing configuration and create a CostTracker."""

import logging
import os
from pathlib import Path

import yaml

from config.feature_flags import apply_mode_overrides
from config.model_routing import TEST_MODEL_ID, _cheap_default
from core.budget import CostTracker

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_mode(mode: str) -> tuple[dict, CostTracker]:
    modes_path = CONFIG_DIR / "modes.yaml"
    prices_path = Path(os.getenv("PRICES_PATH", CONFIG_DIR / "prices.yaml"))

    with open(modes_path) as fh:
        modes = yaml.safe_load(fh) or {}
    if mode not in modes:
        logging.warning("Requested mode '%s' not found. Falling back to 'test'.", mode)
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
        models = mode_cfg.get("models")
        if not (
            isinstance(models, dict)
            and all(stage in models for stage in ["plan", "exec", "synth"])
        ):
            cheap = TEST_MODEL_ID or _cheap_default(prices.get("models", {}))
            mode_cfg["models"] = {s: cheap for s in ["plan", "exec", "synth"]}
    # FAISS defaults and env overrides
    mode_cfg.setdefault("faiss_index_local_dir", ".faiss_index")
    mode_cfg.setdefault("faiss_bootstrap_mode", "download")
    env_uri = os.getenv("FAISS_INDEX_URI")
    if env_uri:
        mode_cfg["faiss_index_uri"] = env_uri
    env_dir = os.getenv("FAISS_INDEX_DIR")
    if env_dir:
        mode_cfg["faiss_index_local_dir"] = env_dir
    env_boot = os.getenv("FAISS_BOOTSTRAP_MODE")
    if env_boot:
        mode_cfg["faiss_bootstrap_mode"] = env_boot

    budget = CostTracker(mode_cfg, prices)
    apply_mode_overrides(mode_cfg)
    return mode_cfg, budget
