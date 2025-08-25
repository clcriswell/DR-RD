"""Load runtime configuration profiles and create a :class:`CostTracker`.

``load_profile()`` is the canonical entry point for loading the single
"Standard" profile. ``load_mode()`` is retained as a deprecated alias for one
release to avoid breaking imports.
"""

import logging
import os
from pathlib import Path

import yaml

from config.feature_flags import apply_overrides
from core.budget import CostTracker

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_profile(mode: str | None = None) -> tuple[dict, CostTracker]:
    """Load the ``standard`` profile and return its config and budget tracker.

    Legacy mode names (``test`` and ``deep``) map to ``standard`` with a
    deprecation warning. Any unknown or missing mode also falls back to
    ``standard`` with a warning.
    """
    env_mode = os.getenv("DRRD_MODE")
    if env_mode and env_mode.lower() != "standard":
        logging.warning("DRRD_MODE '%s' is deprecated and maps to 'standard'.", env_mode)
    if mode is None:
        mode = env_mode

    modes_path = CONFIG_DIR / "modes.yaml"
    prices_path = Path(os.getenv("PRICES_PATH", CONFIG_DIR / "prices.yaml"))

    with open(modes_path) as fh:
        modes = yaml.safe_load(fh) or {}

    requested = mode
    if mode in {"test", "deep"}:
        logging.warning("Mode '%s' is deprecated and maps to 'standard'.", mode)
        mode = "standard"
    if not mode or mode not in modes:
        logging.warning("Requested mode '%s' not found. Falling back to 'standard'.", requested)
        mode = "standard"

    mode_cfg = modes.get(mode, {})
    weights = mode_cfg.get("stage_weights")
    if isinstance(weights, dict):
        total = sum(weights.values())
        if abs(total - 1.0) > 0.05 and total > 0:
            logging.warning("stage_weights for profile %s sum to %.3f; normalizing", mode, total)
            mode_cfg["stage_weights"] = {k: v / total for k, v in weights.items()}

    with open(prices_path) as fh:
        prices = yaml.safe_load(fh) or {}

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
    apply_overrides(mode_cfg)
    return mode_cfg, budget


def load_mode(mode: str) -> tuple[dict, CostTracker]:
    """Deprecated alias for :func:`load_profile`."""

    logging.warning("app.config_loader.load_mode() is deprecated; use load_profile().")
    return load_profile(mode)
