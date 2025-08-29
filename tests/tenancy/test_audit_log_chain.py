from __future__ import annotations

import json

from core import audit_log
from dr_rd.tenancy import models


def test_audit_chain(tmp_path, monkeypatch):
    ctx = models.TenantContext(
        org_id="o",
        workspace_id="w",
        principal=models.Principal(principal_id="p", kind="user", org_id="o", workspace_id="w", roles=[]),
        run_id="r",
    )
    monkeypatch.setenv("AUDIT_HMAC_KEY", "secret")

    def _path(_ctx):
        return tmp_path / "audit.jsonl"

    monkeypatch.setattr(audit_log, "_audit_path", _path)
    audit_log.append_event(ctx, "create", "res1", "ok", {"a": 1})
    audit_log.append_event(ctx, "delete", "res2", "ok", {"b": 2})
    path = tmp_path / "audit.jsonl"
    assert audit_log.verify_chain(path)
    lines = path.read_text().splitlines()
    tampered = json.loads(lines[1])
    tampered["action"] = "nope"
    lines[1] = json.dumps(tampered)
    path.write_text("\n".join(lines) + "\n")
    assert not audit_log.verify_chain(path)
