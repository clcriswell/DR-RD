"""Load runtime configuration profiles and create a :class:`CostTracker`.

Only a single ``standard`` profile is supported. Any legacy mode parameters
or ``DRRD_MODE`` environment variable are ignored.
"""

import logging
from pathlib import Path

import yaml

from config.feature_flags import apply_overrides
from core.budget import CostTracker
from dr_rd.config.env import get_env

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_profile(_mode: str | None = None) -> tuple[dict, CostTracker]:
    """Load the ``standard`` profile and return its config and budget tracker."""
    modes_path = CONFIG_DIR / "modes.yaml"
    prices_path = Path(get_env("PRICES_PATH", str(CONFIG_DIR / "prices.yaml")))

    with open(modes_path) as fh:
        modes = yaml.safe_load(fh) or {}

    mode_cfg = modes.get("standard", {})
    weights = mode_cfg.get("stage_weights")
    if isinstance(weights, dict):
        total = sum(weights.values())
        if abs(total - 1.0) > 0.05 and total > 0:
            logging.warning(
                "stage_weights for profile %s sum to %.3f; normalizing", "standard", total
            )
            mode_cfg["stage_weights"] = {k: v / total for k, v in weights.items()}

    with open(prices_path) as fh:
        prices = yaml.safe_load(fh) or {}

    # FAISS defaults and env overrides
    mode_cfg.setdefault("faiss_index_local_dir", ".faiss_index")
    mode_cfg.setdefault("faiss_bootstrap_mode", "download")
    env_uri = get_env("FAISS_INDEX_URI")
    if env_uri:
        mode_cfg["faiss_index_uri"] = env_uri
    env_dir = get_env("FAISS_INDEX_DIR")
    if env_dir:
        mode_cfg["faiss_index_local_dir"] = env_dir
    env_boot = get_env("FAISS_BOOTSTRAP_MODE")
    if env_boot:
        mode_cfg["faiss_bootstrap_mode"] = env_boot

    budget = CostTracker(mode_cfg, prices)
    apply_overrides(mode_cfg)
    return mode_cfg, budget


def load_mode(mode: str) -> tuple[dict, CostTracker]:
    """Deprecated alias for :func:`load_profile`."""

    logging.warning("app.config_loader.load_mode() is deprecated; use load_profile().")
    return load_profile(mode)
