"""PlannerAgent wrapper exposing a minimal LLM-style interface."""

from __future__ import annotations

import json
from typing import Optional

from dr_rd.agents.planner_agent import (
    PlannerAgent as _PlannerAgent,
    llm_call,
    run_planner,
)


class PlannerAgent(_PlannerAgent):
    """Subclass of the legacy planner with an ``act`` method.

    The underlying planner operates via :func:`run_planner`.  This wrapper adds
    an ``act`` method so the agent can be used interchangeably with
    :class:`core.agents.base_agent.LLMRoleAgent` in tests and orchestration code.
    """

    def __init__(self, model: str = "gpt-5", repair_model: Optional[str] = "gpt-5"):
        super().__init__(model, repair_model)
        self.name = "Planner"

    def act(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Run the planner and return its JSON output as a string."""

        data = self.run(user_prompt, "", roles=None)
        return json.dumps(data)


__all__ = ["PlannerAgent", "llm_call", "run_planner"]
