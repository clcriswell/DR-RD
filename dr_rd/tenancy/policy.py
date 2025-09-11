from __future__ import annotations

from typing import Iterable

from .models import TenantContext

OWNER = "OWNER"
ADMIN = "ADMIN"
RUNNER = "RUNNER"
VIEWER = "VIEWER"
AUDITOR = "AUDITOR"
CONFIG = "CONFIG"


def _has_role(ctx: TenantContext, roles: Iterable[str]) -> bool:
    principal = ctx.principal if ctx else None
    if principal is None or principal.disabled:
        return False
    return any(role in principal.roles for role in roles)


def can_execute(ctx: TenantContext) -> bool:
    return _has_role(ctx, {OWNER, ADMIN, RUNNER})


def can_read_kb(ctx: TenantContext) -> bool:
    return _has_role(ctx, {OWNER, ADMIN, RUNNER, VIEWER})


def can_manage_keys(ctx: TenantContext) -> bool:
    return _has_role(ctx, {OWNER, ADMIN, CONFIG})


def can_view_audit(ctx: TenantContext) -> bool:
    return _has_role(ctx, {OWNER, ADMIN, AUDITOR})


def can_edit_config(ctx: TenantContext) -> bool:
    return _has_role(ctx, {OWNER, ADMIN, CONFIG})
