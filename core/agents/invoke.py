"""Agent invocation utilities."""
from typing import Callable

CALL_ATTRS = ("run", "invoke", "__call__")


def resolve_invoker(agent) -> Callable:
    """Return the first callable attr from CALL_ATTRS or raise TypeError."""
    for name in CALL_ATTRS:
        fn = getattr(agent, name, None)
        if callable(fn):
            return fn
    raise TypeError(
        f"{type(agent).__name__} has no callable interface (expected one of {CALL_ATTRS})"
    )
