from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, asdict

from dr_rd.config.env import get_env
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from dr_rd.tenancy.models import TenantContext


@dataclass
class AuditEvent:
    ts: float
    actor: str
    action: str
    resource: str
    outcome: str
    details_hash: str
    prev_hash: str
    hash: str


@dataclass
class RedactionEvent:
    ts: float
    event: str
    target_hash: str
    reason: str
    redaction_token: str
    prev_hash: str
    hash: str


_DEF_KEY = "dummy_audit_key"


def _get_key() -> str:
    return get_env("AUDIT_HMAC_KEY", _DEF_KEY)


def _hmac(data: str) -> str:
    return hmac.new(_get_key().encode(), data.encode(), hashlib.sha256).hexdigest()


def _audit_path(ctx: TenantContext) -> Path:
    ws = ctx.workspace_id or "_"
    base = Path.home() / ".dr_rd" / "tenants" / ctx.org_id / ws / "audit"
    base.mkdir(parents=True, exist_ok=True)
    return base / "audit.jsonl"


def append_event(ctx: TenantContext, action: str, resource: str, outcome: str, details: Optional[dict] = None) -> AuditEvent:
    path = _audit_path(ctx)
    prev_hash = ""
    if path.exists():
        with path.open() as f:
            for line in f:
                pass
            if line.strip():
                prev_hash = json.loads(line)["hash"]
    details_hash = _hmac(json.dumps(details or {}, sort_keys=True))
    record = {
        "ts": time.time(),
        "actor": ctx.principal.principal_id if ctx.principal else "anonymous",
        "action": action,
        "resource": resource,
        "outcome": outcome,
        "details_hash": details_hash,
        "prev_hash": prev_hash,
    }
    payload = json.dumps(record, sort_keys=True)
    record["hash"] = _hmac(prev_hash + payload)
    with path.open("a") as f:
        f.write(json.dumps(record) + "\n")
    return AuditEvent(**record)


def append_redaction(ctx: TenantContext, target_hash: str, reason: str, redaction_token: str) -> RedactionEvent:
    path = _audit_path(ctx)
    prev_hash = ""
    if path.exists():
        with path.open() as f:
            for line in f:
                pass
            if line.strip():
                prev_hash = json.loads(line)["hash"]
    record = {
        "ts": time.time(),
        "event": "REDACTION",
        "target_hash": target_hash,
        "reason": reason,
        "redaction_token": redaction_token,
        "prev_hash": prev_hash,
    }
    payload = json.dumps(record, sort_keys=True)
    record["hash"] = _hmac(prev_hash + payload)
    with path.open("a") as f:
        f.write(json.dumps(record) + "\n")
    return RedactionEvent(**record)


def verify_chain(path: Path) -> bool:
    prev_hash = ""
    if not path.exists():
        return True
    with path.open() as f:
        for line in f:
            rec = json.loads(line)
            payload = json.dumps({k: rec[k] for k in rec if k != "hash"}, sort_keys=True)
            expected = _hmac(prev_hash + payload)
            if not hmac.compare_digest(expected, rec["hash"]):
                return False
            prev_hash = rec["hash"]
    return True
