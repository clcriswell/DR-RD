from __future__ import annotations

from pathlib import Path

import pytest
from dr_rd.tenancy import models
from dr_rd.config import loader


def test_overlay_precedence(tmp_path, monkeypatch):
    base = tmp_path / "config"
    tenant_dir = base / "tenants" / "o" / "w"
    standard_dir = base / "profiles" / "standard"
    base.mkdir(parents=True)
    tenant_dir.mkdir(parents=True)
    standard_dir.mkdir(parents=True)
    (base / "foo.yaml").write_text("a: 1\n")
    (standard_dir / "foo.yaml").write_text("b: 3\n")
    (tenant_dir / "foo.yaml").write_text("b: 4\n")
    monkeypatch.setenv("DRRD_CONFIG_FOO", "b: 5\nc: 6")
    loader.BASE_CONFIG_DIR = base
    loader.TENANT_CONFIG_DIR = base / "tenants"
    ctx = models.TenantContext(org_id="o", workspace_id="w", principal=None, run_id="r")
    data = loader.load_config("foo", ctx=ctx, profile="standard")
    assert data == {"a": 1, "b": 5, "c": 6}
    with pytest.raises(ValueError):
        loader.load_config("foo", profile="p1")
