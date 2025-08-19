from copy import deepcopy

PROFILES = {
    "deep": {
        "PARALLEL_EXEC_ENABLED": True,
        "TOT_PLANNING_ENABLED": True, "TOT_K": 4, "TOT_BEAM": 3, "TOT_MAX_DEPTH": 3,
        "EVALUATORS_ENABLED": True, "EVALUATOR_MIN_OVERALL": 0.70,
        "REFLECTION_ENABLED": True, "REFLECTION_PATIENCE": 1,
        "RAG_ENABLED": True, "RAG_TOPK": 8, "RAG_SNIPPET_TOKENS": 180,
        "SIM_OPTIMIZER_ENABLED": True, "SIM_OPTIMIZER_STRATEGY": "random", "SIM_OPTIMIZER_MAX_EVALS": 30,
        "IMAGES_SIZE": "256x256",
    },
}

PROFILES["test"] = deepcopy(PROFILES["deep"])

# Backward compatibility: treat "explore" as "deep"
PROFILES["explore"] = PROFILES["deep"]

# UI presets baked into the three modes. The app reads these to hide knobs.
UI_PRESETS = {
    "deep":     {"simulate_enabled": True,  "design_depth": "High",   "refinement_rounds": 3, "rerun_sims_each_round": True,  "estimator": {"exec_tokens": 90000, "help_prob": 0.50}},
}
UI_PRESETS["test"] = UI_PRESETS["deep"]


def apply_profile(env_defaults: dict, mode: str, overrides: dict | None = None) -> dict:
    out = deepcopy(env_defaults)
    profile = PROFILES.get(mode.lower().strip(), {})
    out.update(profile)
    if overrides:
        out.update({k: v for k, v in overrides.items() if v is not None})
    return out

