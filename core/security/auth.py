from __future__ import annotations

import hmac
import hashlib
import os
import secrets
import time
import uuid
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Optional

from dr_rd.tenancy.models import Principal
from dr_rd.config.env import get_env

BASE_DIR = Path.home() / ".dr_rd" / "tenants"
BASE_DIR.mkdir(parents=True, exist_ok=True)
KEYS_PATH = BASE_DIR / "keys.jsonl"


@dataclass
class ApiKey:
    key_id: str
    org_id: str
    workspace_id: Optional[str] = None
    roles: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: time.time())
    last_used_at: Optional[float] = None
    disabled: bool = False
    hashed_secret: str = ""


def _hash_secret(secret: str) -> str:
    salt = get_env("APIKEY_HASH_SALT", "drrd_salt") or "drrd_salt"
    return hmac.new(salt.encode(), secret.encode(), hashlib.sha256).hexdigest()


def _append_record(rec: dict) -> None:
    KEYS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with KEYS_PATH.open("a") as f:
        f.write(json.dumps(rec) + "\n")


def _read_all() -> list[dict]:
    if not KEYS_PATH.exists():
        return []
    with KEYS_PATH.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def create_api_key(
    org_id: str,
    workspace_id: Optional[str] = None,
    roles: Optional[Iterable[str]] = None,
) -> tuple[ApiKey, str]:
    """Create a new API key returning (record, secret)."""
    secret = "drrd_" + secrets.token_urlsafe(20)[:32]
    record = ApiKey(
        key_id=uuid.uuid4().hex,
        org_id=org_id,
        workspace_id=workspace_id,
        roles=list(roles or []),
        hashed_secret=_hash_secret(secret),
    )
    _append_record(asdict(record))
    return record, secret


def verify_api_key(secret: str) -> Optional[Principal]:
    hashed = _hash_secret(secret)
    for rec in _read_all():
        if hmac.compare_digest(rec["hashed_secret"], hashed) and not rec.get("disabled"):
            principal = Principal(
                principal_id=rec["key_id"],
                kind="api_key",
                org_id=rec["org_id"],
                workspace_id=rec.get("workspace_id"),
                roles=rec.get("roles", []),
                disabled=rec.get("disabled", False),
                meta={"api_key": True},
            )
            return principal
    return None
