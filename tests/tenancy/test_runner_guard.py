from __future__ import annotations

import pytest

from core.security.guard import require_perm
from dr_rd.tenancy import context, models


@require_perm("execute")
def _run() -> str:
    return "ok"


def test_execution_allowed():
    ctx = models.TenantContext(
        org_id="o",
        workspace_id="w",
        principal=models.Principal(principal_id="p", kind="user", org_id="o", workspace_id="w", roles=["RUNNER"]),
        run_id="r",
    )
    assert context.with_tenant(ctx, _run) == "ok"


def test_execution_denied():
    ctx = models.TenantContext(
        org_id="o",
        workspace_id="w",
        principal=models.Principal(principal_id="p", kind="user", org_id="o", workspace_id="w", roles=["VIEWER"]),
        run_id="r",
    )
    with pytest.raises(PermissionError):
        context.with_tenant(ctx, _run)
