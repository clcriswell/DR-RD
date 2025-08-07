from __future__ import annotations

import os


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

# Parameters for Tree-of-Thoughts planning. These remain inexpensive to
# access even when the feature flag is disabled.
TOT_K: int = int(os.getenv("TOT_K", "3"))
TOT_BEAM: int = int(os.getenv("TOT_BEAM", "2"))
TOT_MAX_DEPTH: int = int(os.getenv("TOT_MAX_DEPTH", "2"))

# Reflection parameters
REFLECTION_PATIENCE: int = int(os.getenv("REFLECTION_PATIENCE", "2"))
REFLECTION_MAX_ATTEMPTS: int = int(os.getenv("REFLECTION_MAX_ATTEMPTS", "1"))
