from __future__ import annotations

from functools import wraps
from typing import Callable

from dr_rd.tenancy.context import require_tenant
from dr_rd.tenancy import policy

PERMISSIONS = {
    "execute": policy.can_execute,
    "read_kb": policy.can_read_kb,
    "manage_keys": policy.can_manage_keys,
    "view_audit": policy.can_view_audit,
    "edit_config": policy.can_edit_config,
}


def require_perm(name: str) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """Decorator enforcing that current tenant has the given permission."""
    if name not in PERMISSIONS:
        raise KeyError(f"unknown permission {name}")

    def decorator(fn: Callable[..., object]) -> Callable[..., object]:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ctx = require_tenant()
            if not PERMISSIONS[name](ctx):
                raise PermissionError(f"tenant lacks permission: {name}")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
