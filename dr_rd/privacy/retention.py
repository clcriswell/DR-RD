from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import yaml

from .pii import redact_text

_CFG_PATH = Path("config/retention.yaml")
_CFG = yaml.safe_load(_CFG_PATH.read_text()) if _CFG_PATH.exists() else {}


_DEF_REGISTRY = {
    "kb": "kb",
    "rag_index": "rag_index",
    "provenance": "provenance",
    "telemetry": "telemetry",
    "audit": "audit",
    "cache": "cache",
    "examples": "examples",
    "incidents": "incidents",
    "billing": "billing",
}


def _tenant_root(tenant: tuple[str, str]) -> Path:
    org, ws = tenant
    return Path.home() / ".dr_rd" / "tenants" / org / ws


def _privacy_dir(tenant: tuple[str, str]) -> Path:
    d = _tenant_root(tenant) / "privacy" / "receipts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_receipt(tenant: tuple[str, str], name: str, data: Dict[str, Any]) -> Path:
    path = _privacy_dir(tenant) / f"{name}-{int(datetime.utcnow().timestamp())}.json"
    path.write_text(json.dumps(data, indent=2))
    return path


def sweep_ttl(tenant: tuple[str, str], now: datetime, cfg: Dict[str, Any]) -> Dict[str, int]:
    report: Dict[str, int] = {}
    root = _tenant_root(tenant)
    retention = cfg.get("privacy", {}).get("retention", {})
    for store, ttl_key in {
        "kb": "kb_days",
        "provenance": "provenance_days",
        "telemetry": "telemetry_days",
        "audit": "audit_days",
        "rag_index": "rag_index_days",
        "cache": "cache_days",
        "incidents": "incidents_days",
        "billing": "billing_days",
    }.items():
        ttl = retention.get(ttl_key)
        if ttl is None:
            continue
        path = root / _DEF_REGISTRY.get(store, store)
        cutoff = now - timedelta(days=int(ttl))
        removed = 0
        if path.exists():
            for f in path.rglob("*"):
                if f.is_file() and datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                    f.unlink()
                    removed += 1
        report[store] = removed
    _write_receipt(tenant, "sweep_ttl", report)
    return report


def scrub_pii(tenant: tuple[str, str], cfg: Dict[str, Any]) -> Dict[str, int]:
    token = cfg.get("privacy", {}).get("erase", {}).get("redaction_token", "[REDACTED]")
    report: Dict[str, int] = {}
    root = _tenant_root(tenant)
    for store in ["kb", "rag_index", "cache"]:
        path = root / _DEF_REGISTRY.get(store, store)
        redacted = 0
        if path.exists():
            for f in path.rglob("*.txt"):
                try:
                    txt = f.read_text()
                except Exception:
                    continue
                new_txt = redact_text(txt, token)
                if new_txt != txt:
                    f.write_text(new_txt)
                    redacted += 1
        report[store] = redacted
    _write_receipt(tenant, "scrub_pii", report)
    return report
