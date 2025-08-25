from copy import deepcopy
import logging

PROFILES = {
    "standard": {
        "ENABLE_LIVE_SEARCH": True,
        "PARALLEL_EXEC_ENABLED": True,
        "TOT_PLANNING_ENABLED": True,
        "TOT_K": 4,
        "TOT_BEAM": 3,
        "TOT_MAX_DEPTH": 3,
        "EVALUATORS_ENABLED": True,
        "EVALUATOR_MIN_OVERALL": 0.70,
        "REFLECTION_ENABLED": True,
        "REFLECTION_PATIENCE": 1,
        "RAG_ENABLED": True,
        "RAG_TOPK": 8,
        "SIM_OPTIMIZER_ENABLED": True,
        "SIM_OPTIMIZER_STRATEGY": "random",
        "SIM_OPTIMIZER_MAX_EVALS": 30,
        "IMAGES_SIZE": "256x256",
    }
}
PROFILES["deep"] = PROFILES["standard"]
PROFILES["test"] = PROFILES["standard"]

UI_PRESETS = {
    "standard": {
        "simulate_enabled": True,
        "design_depth": "High",
        "refinement_rounds": 3,
        "rerun_sims_each_round": True,
        "estimator": {"exec_tokens": 90000, "help_prob": 0.50},
    }
}
UI_PRESETS["deep"] = UI_PRESETS["standard"]
UI_PRESETS["test"] = UI_PRESETS["standard"]


def apply_profile(env_defaults: dict, mode: str, overrides: dict | None = None) -> dict:
    """Merge defaults with the selected profile and overrides.

    Legacy modes ``deep`` and ``test`` map to ``standard``; they are deprecated and will be
    removed in a future release. For compatibility, ``mode='test'`` also injects
    ``TEST_MODE=True``. This shim will be removed in a later step.
    """
    orig_mode = (mode or "standard").strip().lower()
    canonical_mode = "standard" if orig_mode in {"deep", "test"} else orig_mode
    if orig_mode in {"deep", "test"}:
        logging.warning("Mode '%s' is deprecated; using 'standard' profile.", orig_mode)

    out = deepcopy(env_defaults)
    profile = PROFILES.get(canonical_mode, {})
    out.update(profile)

    if orig_mode == "test":
        out["TEST_MODE"] = True

    if overrides:
        out.update({k: v for k, v in overrides.items() if v is not None})

    return out
