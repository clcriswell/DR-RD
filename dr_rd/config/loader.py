from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from dr_rd.tenancy.models import TenantContext

BASE_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
TENANT_CONFIG_DIR = BASE_CONFIG_DIR / "tenants"


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open() as f:
        data = yaml.safe_load(f) or {}
    return data


def _merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            a[k] = _merge(a.get(k, {}), v)
        else:
            a[k] = v
    return a


def load_config(name: str, ctx: Optional[TenantContext] = None, profile: Optional[str] = None) -> Dict[str, Any]:
    """Load a configuration file applying overlays in the proper order."""
    config = _load_yaml(BASE_CONFIG_DIR / f"{name}.yaml")
    if profile:
        config = _merge(config, _load_yaml(BASE_CONFIG_DIR / "profiles" / profile / f"{name}.yaml"))
    if ctx:
        overlay = TENANT_CONFIG_DIR / ctx.org_id / (ctx.workspace_id or "_") / f"{name}.yaml"
        config = _merge(config, _load_yaml(overlay))
    env_override = os.getenv(f"DRRD_CONFIG_{name.upper()}")
    if env_override:
        config = _merge(config, yaml.safe_load(env_override))
    return config
