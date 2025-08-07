from __future__ import annotations

import os


def _flag(name: str) -> bool:
    return os.getenv(name, "false").lower() == "true"


EVALUATORS_ENABLED = _flag("EVALUATORS_ENABLED")
PARALLEL_EXEC_ENABLED = _flag("PARALLEL_EXEC_ENABLED")
TOT_PLANNING_ENABLED = _flag("TOT_PLANNING_ENABLED")
REFLECTION_ENABLED = _flag("REFLECTION_ENABLED")
SIM_OPTIMIZER_ENABLED = _flag("SIM_OPTIMIZER_ENABLED")
RAG_ENABLED = _flag("RAG_ENABLED")
