from __future__ import annotations

from contextvars import ContextVar
from functools import wraps
from typing import Callable, TypeVar, Any

from .models import TenantContext

_T = TypeVar("_T")

_tenant_ctx: ContextVar[TenantContext | None] = ContextVar("tenant_ctx", default=None)


def current_tenant() -> TenantContext | None:
    """Return the current tenant context if one has been set."""
    return _tenant_ctx.get()


def set_current_tenant(ctx: TenantContext | None) -> None:
    _tenant_ctx.set(ctx)


def require_tenant() -> TenantContext:
    """Fetch the active tenant context or raise."""
    ctx = current_tenant()
    if ctx is None:
        raise RuntimeError("tenant context is required")
    return ctx


def with_tenant(ctx: TenantContext, fn: Callable[..., _T], *args: Any, **kwargs: Any) -> _T:
    """Execute ``fn`` with ``ctx`` active as the tenant context."""
    token = _tenant_ctx.set(ctx)
    try:
        return fn(*args, **kwargs)
    finally:
        _tenant_ctx.reset(token)


def tenant_context(ctx: TenantContext) -> Callable[[Callable[..., _T]], Callable[..., _T]]:
    """Decorator to run a function with a given tenant context."""

    def decorator(fn: Callable[..., _T]) -> Callable[..., _T]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> _T:
            return with_tenant(ctx, fn, *args, **kwargs)

        return wrapper

    return decorator
