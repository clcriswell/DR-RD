from __future__ import annotations

import importlib
from pathlib import Path

from dr_rd.tenancy import context, models, store


def _patch_base(tmp_path: Path) -> None:
    store.BASE_DIR = tmp_path


def test_store_and_context(tmp_path):
    _patch_base(tmp_path)
    org = store.create_org("Acme")
    ws = store.create_workspace(org.org_id, "Lab")
    principal = store.create_principal("p1", "user", org.org_id, ws.workspace_id, roles=["RUNNER"])
    ctx = models.TenantContext(org_id=org.org_id, workspace_id=ws.workspace_id, principal=principal, run_id="r1")

    def inner():
        return context.require_tenant()

    result = context.with_tenant(ctx, inner)
    assert result.org_id == org.org_id
    assert store.get_workspace(org.org_id, ws.workspace_id).workspace_id == ws.workspace_id
