from typing import Any, Dict, List


def evaluate(summary: Dict[str, Any], targets: Dict[str, float] | None = None) -> Dict[str, Any]:
    targets = targets or {}
    breaches: List[Dict[str, Any]] = []
    for key, budget in summary.get("budget_remaining", {}).items():
        target = targets.get(key, budget.get("target"))
        remaining = budget.get("remaining", 0)
        if remaining < 0:
            breaches.append({"sli": key, "remaining": remaining, "target": target})
    return {"sli_values": summary.get("sli_values", {}), "budget_remaining": summary.get("budget_remaining", {}), "breaches": breaches}
