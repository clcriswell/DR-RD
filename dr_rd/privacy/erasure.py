from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict

from .retention import _tenant_root, _write_receipt

from core import audit_log
from core import provenance
from dr_rd.tenancy.models import TenantContext


def _req_dir(tenant: tuple[str, str]) -> Path:
    root = _tenant_root(tenant) / "privacy"
    root.mkdir(parents=True, exist_ok=True)
    return root


def mark_subject_for_erasure(
    tenant: tuple[str, str], subject_key: str, reason: str, requested_by: str
) -> str:
    request_id = uuid.uuid4().hex
    data = {
        "id": request_id,
        "subject_key": subject_key,
        "reason": reason,
        "requested_by": requested_by,
        "ts": time.time(),
        "status": "pending",
    }
    path = _req_dir(tenant) / "erasure_requests.jsonl"
    with path.open("a") as f:
        f.write(json.dumps(data) + "\n")
    _write_receipt(tenant, f"mark_{request_id}", data)
    return request_id


def preview_impact(tenant: tuple[str, str], subject_key: str) -> Dict[str, int]:
    root = _tenant_root(tenant)
    counts: Dict[str, int] = {}
    for f in root.rglob("*"):
        if f.is_file():
            try:
                txt = f.read_text()
            except Exception:
                continue
            if subject_key in txt:
                counts[str(f)] = counts.get(str(f), 0) + 1
    _write_receipt(tenant, "preview", counts)
    return counts


def execute_erasure(tenant: tuple[str, str], subject_key: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    token = cfg.get("privacy", {}).get("erase", {}).get("redaction_token", "[REDACTED]")
    root = _tenant_root(tenant)
    touched = []
    for f in root.rglob("*"):
        if f.is_file():
            try:
                txt = f.read_text()
            except Exception:
                continue
            if subject_key in txt:
                new_txt = txt.replace(subject_key, token)
                f.write_text(new_txt)
                touched.append(str(f))
                h = hashlib.sha256((str(f) + subject_key).encode()).hexdigest()
                ctx = TenantContext(org_id=tenant[0], workspace_id=tenant[1])
                audit_log.append_redaction(ctx, h, "ERASURE_REQUEST", token)
                provenance.append_redaction_event(h, "ERASURE_REQUEST", token)
    receipt = {"subject_key": subject_key, "files": touched, "ts": time.time()}
    _write_receipt(tenant, "execute", receipt)
    return receipt
