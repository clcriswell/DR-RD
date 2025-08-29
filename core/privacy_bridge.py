from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from dr_rd.privacy import (
    derive_subject_key,
    sweep_ttl,
    scrub_pii,
    mark_subject_for_erasure,
    execute_erasure,
    export_tenant,
    export_subject,
)
from config import feature_flags
import yaml
import os

_CFG_PATH = "config/retention.yaml"
CFG = yaml.safe_load(open(_CFG_PATH)) if feature_flags.PRIVACY_ENABLED and os.path.exists(_CFG_PATH) else {}


def run_scheduled_privacy_jobs(tenant: tuple[str, str], now: datetime, cfg: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ttl": sweep_ttl(tenant, now, cfg),
        "scrub": scrub_pii(tenant, cfg),
    }


def start_subject_erasure(tenant: tuple[str, str], subject: Dict[str, str] | str) -> Dict[str, Any]:
    fields = CFG.get("privacy", {}).get("identifiers", {}).get("fields", [])
    salt_env = CFG.get("privacy", {}).get("identifiers", {}).get("subject_salt_env", "PRIVACY_SALT")
    if isinstance(subject, str):
        subject_key = subject
    else:
        subject_key = derive_subject_key(subject, fields, salt_env) or subject.get("subject_key")
    mark_subject_for_erasure(tenant, subject_key, "REQUESTED", "system")
    return execute_erasure(tenant, subject_key, CFG)


def export_for_tenant(tenant: tuple[str, str]) -> str:
    return str(export_tenant(tenant))


def export_for_subject(tenant: tuple[str, str], subject_key: str) -> str:
    return str(export_subject(tenant, subject_key))
