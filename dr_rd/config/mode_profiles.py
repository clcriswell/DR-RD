from copy import deepcopy

PROFILES = {
    "fast": {
        "PARALLEL_EXEC_ENABLED": True,
        "TOT_PLANNING_ENABLED": False,
        "EVALUATORS_ENABLED": False,
        "REFLECTION_ENABLED": False,
        "RAG_ENABLED": False,
        "SIM_OPTIMIZER_ENABLED": False,
    },
    "balanced": {
        "PARALLEL_EXEC_ENABLED": True,
        "TOT_PLANNING_ENABLED": True, "TOT_K": 3, "TOT_BEAM": 2, "TOT_MAX_DEPTH": 2,
        "EVALUATORS_ENABLED": True, "EVALUATOR_MIN_OVERALL": 0.60,
        "REFLECTION_ENABLED": True, "REFLECTION_PATIENCE": 2,
        "RAG_ENABLED": True, "RAG_TOPK": 4, "RAG_SNIPPET_TOKENS": 120,
        "SIM_OPTIMIZER_ENABLED": False,
    },
    "explore": {
        "PARALLEL_EXEC_ENABLED": True,
        "TOT_PLANNING_ENABLED": True, "TOT_K": 5, "TOT_BEAM": 3, "TOT_MAX_DEPTH": 3,
        "EVALUATORS_ENABLED": True, "EVALUATOR_MIN_OVERALL": 0.70,
        "REFLECTION_ENABLED": True, "REFLECTION_PATIENCE": 1,
        "RAG_ENABLED": True, "RAG_TOPK": 8, "RAG_SNIPPET_TOKENS": 180,
        "SIM_OPTIMIZER_ENABLED": True, "SIM_OPTIMIZER_STRATEGY": "random", "SIM_OPTIMIZER_MAX_EVALS": 30,
    },
}

def apply_profile(env_defaults: dict, mode: str, overrides: dict | None = None) -> dict:
    out = deepcopy(env_defaults)
    profile = PROFILES.get(mode.lower().strip(), {})
    out.update(profile)
    if overrides:
        out.update({k: v for k, v in overrides.items() if v is not None})
    return out
