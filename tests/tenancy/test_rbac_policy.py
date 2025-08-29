from __future__ import annotations

from dr_rd.tenancy import models, policy


def _ctx(roles):
    p = models.Principal(principal_id="p", kind="user", org_id="o", workspace_id="w", roles=roles)
    return models.TenantContext(org_id="o", workspace_id="w", principal=p, run_id="r")


def test_permission_matrix():
    assert policy.can_execute(_ctx(["RUNNER"]))
    assert policy.can_read_kb(_ctx(["VIEWER"]))
    assert not policy.can_manage_keys(_ctx(["VIEWER"]))
    assert policy.can_manage_keys(_ctx(["OWNER"]))


def test_superuser(monkeypatch):
    ctx = _ctx([])
    assert not policy.can_manage_keys(ctx)
    monkeypatch.setenv("DRRD_SUPERUSER_MODE", "1")
    assert policy.can_manage_keys(ctx)
