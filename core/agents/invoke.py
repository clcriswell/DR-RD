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
    """Invoke ``agent`` with standard keyword arguments.

    The callable is resolved via :func:`resolve_invoker`.  A first attempt is
    made to call the method with ``task``, ``model``, and ``meta`` keywords.  If
    the agent has a stricter signature a second attempt is made with only the
    accepted parameters.
    """

    name = (meta or {}).get("agent") or type(agent).__name__
    method_name, fn = resolve_invoker(agent)
    logger.info("invoke agent=%s via=%s", name, method_name)

    try:
        return fn(task=task, model=model, meta=meta)
    except TypeError:
        sig = inspect.signature(fn)
        kwargs = {}
        if "task" in sig.parameters:
            kwargs["task"] = task
        if "model" in sig.parameters:
            kwargs["model"] = model
        if "meta" in sig.parameters:
            kwargs["meta"] = meta
        return fn(**kwargs)


__all__ = ["CALL_ATTRS", "resolve_invoker", "invoke_agent"]
