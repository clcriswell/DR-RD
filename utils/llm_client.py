from __future__ import annotations

import os
import time
from typing import Any, Iterator, Mapping, Optional

from .providers import fallback_chain, model_key
from .retry import backoff, classify_error, should_retry
from .circuit import status, record_failure, record_success, allow_half_open
from .idempotency import key as idem_key, get as cache_get, put as cache_put
from .telemetry import log_event
from utils import otel


def _call_provider(prov: str, model: str, payload: Mapping[str, Any], *, stream: bool) -> Any:
    """Minimal provider dispatch. Supports OpenAI chat API."""
    if prov == 'openai':
        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover - environment guard
            raise RuntimeError('openai sdk missing') from exc
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        messages = payload.get('messages') or []
        if stream:
            return client.chat.completions.create(model=model, messages=messages, stream=True)
        return client.chat.completions.create(model=model, messages=messages)
    raise NotImplementedError(f'provider {prov} not supported')


def chat(payload: Mapping[str, Any], *, mode: str, stream: bool = False,
         run_id: str | None = None, step_id: str | None = None,
         cache_ttl_sec: Optional[int] = 300) -> Any | Iterator[Any]:
    chain = fallback_chain(mode)
    for prov, model in chain:
        ck = model_key(prov, model)
        k = idem_key(prov, model, payload)
        if not stream:
            cached = cache_get(k, ttl_sec=cache_ttl_sec)
            if cached is not None:
                log_event({"event": "llm_cache_hit", "provider": prov, "model": model,
                           "run_id": run_id, "step_id": step_id})
                return cached
        st = status(ck)
        if st == 'open' and not allow_half_open(ck):
            log_event({"event": "circuit_skipped", "provider": prov, "model": model})
            continue
        attempt = 0
        while True:
            attempt += 1
            try:
                log_event({"event": "llm_call_started", "provider": prov, "model": model,
                           "attempt": attempt, "run_id": run_id, "step_id": step_id})
                with otel.start_span(
                    "llm.call",
                    attrs={
                        "provider": prov,
                        "model": model,
                        "attempt": attempt,
                        "stream": bool(stream),
                        "run_id": run_id,
                        "step_id": step_id,
                    },
                    run_id=run_id,
                ) as span:
                    try:
                        resp = _call_provider(prov, model, payload, stream=stream)
                    except Exception as exc:
                        span.record_exception(exc)
                        raise
                    usage = getattr(resp, "usage", None)
                    if usage:
                        for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
                            val = getattr(usage, k, None)
                            if val is not None:
                                span.set_attribute(k, val)
                    if isinstance(resp, Mapping) and "cost_usd" in resp:
                        span.set_attribute("cost_usd", resp["cost_usd"])
                record_success(ck)
                log_event({"event": "llm_call_succeeded", "provider": prov, "model": model,
                           "attempt": attempt, "run_id": run_id, "step_id": step_id})
                if stream:
                    return resp
                cache_put(k, resp)
                return resp
            except Exception as exc:
                kind = classify_error(exc)
                log_event({"event": "llm_call_failed", "provider": prov, "model": model,
                           "attempt": attempt, "kind": kind,
                           "run_id": run_id, "step_id": step_id})
                if not should_retry(kind) or attempt >= 5:
                    if kind in {"rate_limit", "transient", "timeout"}:
                        record_failure(ck)
                    break
                time.sleep(backoff(attempt))
        log_event({"event": "llm_fallback", "provider": prov, "model": model})
    raise RuntimeError("All providers/models failed")
