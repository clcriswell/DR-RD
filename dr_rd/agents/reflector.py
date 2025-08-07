from __future__ import annotations

from typing import Any, Dict, List

from dr_rd.extensions.abcs import BaseMetaAgent
from dr_rd.extensions.registry import MetaAgentRegistry
from dr_rd.reflection.policy import analyze_history


class ReflectorMetaAgent(BaseMetaAgent):
    """Diagnoses stagnation and proposes strategy adjustments."""

    def reflect(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        return analyze_history(history)


# Register so orchestrators can discover it.
MetaAgentRegistry.register("reflector", ReflectorMetaAgent)
