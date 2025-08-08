from __future__ import annotations

from typing import Any, Dict, List


def analyze_history(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Suggest adjustments based on recent execution ``history``.

    The policy inspects the last few cycles for common failure modes such as
    stagnant scores or repeated simulation failures and returns recommended
    adjustments. Returned keys are interpreted by the orchestrator and may
    include ``switch_to_tot``, ``new_tasks``, ``role_tweak`` or ``reason``.
    """

    if len(history) < 2:
        return {}

    last_two = history[-2:]
    scores = [h.get("score", 0.0) for h in last_two]
    if scores[0] >= scores[1]:
        return {
            "switch_to_tot": True,
            "new_tasks": [
                {
                    "role": "AI R&D Coordinator",
                    "task": "Reassess goals and clarify requirements",
                }
            ],
            "reason": "score plateau over two cycles",
        }

    sim_fails = sum(int(h.get("sim_failures", 0)) for h in last_two)
    if sim_fails >= 2:
        return {
            "role_tweak": {
                "Simulation Agent": "Review constraints and retry with relaxed parameters"
            },
            "reason": "repeated simulation failures",
        }

    return {}
