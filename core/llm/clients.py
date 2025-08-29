from __future__ import annotations

import time
from typing import Any, Dict, Tuple

from core.llm_client import call_openai
from core import provenance
from dr_rd.telemetry import metrics
from .model_router import RouteDecision, failover_policy


def call_model(decision: RouteDecision, prompt_obj: Dict[str, Any], timeout_ms: int) -> Tuple[Any, Dict[str, int]]:
    span = provenance.start_span(
        "model.call",
        {"provider": decision.provider, "model": decision.model, "purpose": prompt_obj.get("purpose")},
    )
    t0 = time.monotonic()
    try:
        if decision.provider == "openai":
            messages = prompt_obj.get("messages", [])
            params = prompt_obj.get("params", {})
            result = call_openai(model=decision.model, messages=messages, **params)
            usage = result.get("usage") or {}
            latency = int((time.monotonic() - t0) * 1000)
            provenance.end_span(span, meta={"latency_ms": latency, "usage": usage})
            metrics.observe(
                "model_call_latency_ms",
                latency,
                provider=decision.provider,
                model=decision.model,
            )
            metrics.observe(
                "tokens_in", usage.get("prompt_tokens", 0), provider=decision.provider, model=decision.model
            )
            metrics.observe(
                "tokens_out", usage.get("completion_tokens", 0), provider=decision.provider, model=decision.model
            )
            return result, usage
        raise NotImplementedError(f"provider {decision.provider} not supported")
    except Exception as e:  # pragma: no cover - pass through
        provenance.end_span(span, ok=False, meta={"error": str(e)})
        metrics.inc("runs_failed", provider=decision.provider, model=decision.model)
        raise


def call_model_with_failover(decision: RouteDecision, prompt_obj: Dict[str, Any], timeout_ms: int) -> Tuple[Any, Dict[str, int]]:
    try:
        return call_model(decision, prompt_obj, timeout_ms)
    except Exception:
        next_decision = failover_policy(decision)
        if next_decision is None:
            raise
        return call_model(next_decision, prompt_obj, timeout_ms)


__all__ = ["call_model", "call_model_with_failover"]
