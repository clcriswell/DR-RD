"""Agent invocation utilities."""

from __future__ import annotations

import inspect
import logging
from typing import Callable, Tuple


logger = logging.getLogger(__name__)

CALL_ATTRS = ("run", "invoke", "__call__")


def resolve_invoker(agent) -> Tuple[str, Callable]:
    """Return the first callable attribute name and function.

    Attributes are searched in ``CALL_ATTRS`` order.  If none are present,
    ``TypeError`` is raised with a clear, standardised message.
    """

    for name in CALL_ATTRS:
        fn = getattr(agent, name, None)
        if callable(fn):
            return name, fn
    raise TypeError(
        f"{type(agent).__name__} has no callable interface (expected one of {CALL_ATTRS})"
    )


def invoke_agent(
    agent, *, task: dict, model: str | None = None, meta: dict | None = None
):
    """Invoke ``agent`` with ``task``/``model``/``meta`` keywords.

    Any parameters not accepted by the agent's callable are dropped before
    invocation.  Errors from the agent are re-raised with contextual details.
    """

    meta = meta or {}
    method_name, method = resolve_invoker(agent)
    logger.info("invoke agent=%s via=%s", meta.get("agent"), method_name)

    try:
        sig = inspect.signature(method)
        kwargs = {}
        if "task" in sig.parameters:
            kwargs["task"] = task
        if "model" in sig.parameters:
            kwargs["model"] = model
        if "meta" in sig.parameters:
            kwargs["meta"] = meta
        return method(**kwargs)
    except Exception as e:  # pragma: no cover - message enrichment
        agent_name = meta.get("agent")
        raise type(e)(
            f"{agent_name} ({type(agent).__name__}.{method_name}) failed: {e}"
        ) from e


__all__ = ["CALL_ATTRS", "resolve_invoker", "invoke_agent"]

