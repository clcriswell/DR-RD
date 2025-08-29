from __future__ import annotations

from pathlib import Path

from dr_rd.tenancy import models
from dr_rd.config import loader


def test_overlay_precedence(tmp_path, monkeypatch):
    base = tmp_path / "config"
    profile_dir = base / "profiles" / "p1"
    tenant_dir = base / "tenants" / "o" / "w"
    base.mkdir(parents=True)
    profile_dir.mkdir(parents=True)
    tenant_dir.mkdir(parents=True)
    (base / "foo.yaml").write_text("a: 1\n")
    (profile_dir / "foo.yaml").write_text("a: 2\nb: 3\n")
    (tenant_dir / "foo.yaml").write_text("b: 4\n")
    monkeypatch.setenv("DRRD_CONFIG_FOO", "b: 5\nc: 6")
    loader.BASE_CONFIG_DIR = base
    loader.TENANT_CONFIG_DIR = base / "tenants"
    ctx = models.TenantContext(org_id="o", workspace_id="w", principal=None, run_id="r")
    data = loader.load_config("foo", ctx=ctx, profile="p1")
    assert data == {"a": 2, "b": 5, "c": 6}
