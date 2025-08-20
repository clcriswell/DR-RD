from __future__ import annotations

import os
import json


def _flag(name: str) -> bool:
    return os.getenv(name, "false").lower() == "true"


EVALUATORS_ENABLED = _flag("EVALUATORS_ENABLED")
PARALLEL_EXEC_ENABLED = _flag("PARALLEL_EXEC_ENABLED")
TOT_PLANNING_ENABLED = _flag("TOT_PLANNING_ENABLED")
REFLECTION_ENABLED = _flag("REFLECTION_ENABLED")
SIM_OPTIMIZER_ENABLED = _flag("SIM_OPTIMIZER_ENABLED")
SIM_OPTIMIZER_STRATEGY: str = os.getenv("SIM_OPTIMIZER_STRATEGY", "random")
SIM_OPTIMIZER_MAX_EVALS: int = int(os.getenv("SIM_OPTIMIZER_MAX_EVALS", "50"))
RAG_ENABLED = _flag("RAG_ENABLED")
RAG_TOPK: int = int(os.getenv("RAG_TOPK", "5"))
ENABLE_LIVE_SEARCH = _flag("ENABLE_LIVE_SEARCH")
DISABLE_IMAGES_BY_DEFAULT = {"test": False, "deep": False}

# Default evaluator weights and threshold. ``EVALUATOR_WEIGHTS`` can be
# overridden via an environment variable containing a JSON object.
EVALUATOR_WEIGHTS = json.loads(
    os.getenv(
        "EVALUATOR_WEIGHTS",
        '{"cost": 0.25, "feasibility": 0.35, "novelty": 0.25, "compliance": 0.15}',
    )
)
EVALUATOR_MIN_OVERALL: float = float(os.getenv("EVALUATOR_MIN_OVERALL", "0.6"))

# Parameters for Tree-of-Thoughts planning. These remain inexpensive to
# access even when the feature flag is disabled.
TOT_K: int = int(os.getenv("TOT_K", "3"))
TOT_BEAM: int = int(os.getenv("TOT_BEAM", "2"))
TOT_MAX_DEPTH: int = int(os.getenv("TOT_MAX_DEPTH", "2"))

# Reflection parameters
REFLECTION_PATIENCE: int = int(os.getenv("REFLECTION_PATIENCE", "2"))
REFLECTION_MAX_ATTEMPTS: int = int(os.getenv("REFLECTION_MAX_ATTEMPTS", "1"))


def get_env_defaults() -> dict:
    return {
        "PARALLEL_EXEC_ENABLED": PARALLEL_EXEC_ENABLED,
        "TOT_PLANNING_ENABLED": TOT_PLANNING_ENABLED,
        "TOT_K": TOT_K,
        "TOT_BEAM": TOT_BEAM,
        "TOT_MAX_DEPTH": TOT_MAX_DEPTH,
        "EVALUATORS_ENABLED": EVALUATORS_ENABLED,
        "EVALUATOR_MIN_OVERALL": (
            EVALUATOR_MIN_OVERALL if "EVALUATOR_MIN_OVERALL" in globals() else 0.0
        ),
        "REFLECTION_ENABLED": REFLECTION_ENABLED,
        "REFLECTION_PATIENCE": REFLECTION_PATIENCE,
        "RAG_ENABLED": RAG_ENABLED,
        "RAG_TOPK": RAG_TOPK,
        "ENABLE_LIVE_SEARCH": ENABLE_LIVE_SEARCH,
        "SIM_OPTIMIZER_ENABLED": SIM_OPTIMIZER_ENABLED,
        "SIM_OPTIMIZER_STRATEGY": SIM_OPTIMIZER_STRATEGY,
        "SIM_OPTIMIZER_MAX_EVALS": SIM_OPTIMIZER_MAX_EVALS,
    }
