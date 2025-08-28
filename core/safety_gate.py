from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

from config import feature_flags
from dr_rd.safety import filters
from dr_rd.policy.engine import evaluate as policy_evaluate, classify


def preflight(text: str) -> List[str]:
    """Classify text for potential risks."""
    return list(classify(text))


def guard_output(
    agent_role: str,
    output_json: Any,
    retry_fn: Callable[[], Any] | None = None,
    evaluator_retry_fn: Callable[[], Any] | None = None,
) -> Tuple[bool, Any, Dict[str, Any]]:
    """Filter output and handle repair attempts.

    Returns ``(ok, json_obj, safety_meta)``.
    """
    sanitized, decision = filters.filter_output(output_json)
    attempts = 0
    max_attempts = filters.SAFETY_CFG.get("repair_max_attempts", 1)
    safety_meta: Dict[str, Any] = {"decision": decision.__dict__, "attempts": attempts}
    if decision.allowed:
        return True, sanitized, safety_meta

    while attempts < max_attempts and retry_fn:
        attempts += 1
        retry_out = retry_fn()
        sanitized, decision = filters.filter_output(retry_out)
        safety_meta = {"decision": decision.__dict__, "attempts": attempts}
        if decision.allowed:
            return True, sanitized, safety_meta

    if (
        not decision.allowed
        and feature_flags.EVALUATORS_ENABLED
        and evaluator_retry_fn
    ):
        attempts += 1
        retry_out = evaluator_retry_fn()
        sanitized, decision = filters.filter_output(retry_out)
        safety_meta = {"decision": decision.__dict__, "attempts": attempts}
        if decision.allowed:
            return True, sanitized, safety_meta

    return False, {"error": "SAFETY_BLOCKED"}, safety_meta
