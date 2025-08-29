from __future__ import annotations

import json
import shutil
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional

from .retention import _tenant_root, _write_receipt


_DEF_COMPONENTS = [
    "kb",
    "provenance",
    "telemetry",
    "audit",
    "configs",
    "index",
    "invoices",
]


def _make_manifest(dest: Path, components: Dict[str, str]) -> None:
    manifest = {"generated_at": time.time(), "components": list(components.keys())}
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2))


def export_tenant(
    tenant: tuple[str, str],
    since: Optional[float] = None,
    until: Optional[float] = None,
    format: str = "zip",
) -> Path:
    root = _tenant_root(tenant)
    temp_dir = Path(tempfile.mkdtemp())
    bundle = temp_dir / "bundle"
    bundle.mkdir()
    copied: Dict[str, str] = {}
    for comp in _DEF_COMPONENTS:
        src = root / comp
        if src.exists():
            dst = bundle / comp
            shutil.copytree(src, dst)
            copied[comp] = str(dst)
    cfg_dir = bundle / "configs"
    cfg_dir.mkdir(exist_ok=True)
    retention_cfg = Path("config/retention.yaml")
    if retention_cfg.exists():
        shutil.copy(retention_cfg, cfg_dir / "retention.yaml")
        copied["configs"] = str(cfg_dir)
    _make_manifest(bundle, copied)
    out_path = temp_dir / "export.zip"
    with zipfile.ZipFile(out_path, "w") as z:
        for f in bundle.rglob("*"):
            z.write(f, f.relative_to(bundle))
    _write_receipt(tenant, "export_tenant", {"path": str(out_path)})
    return out_path


def export_subject(tenant: tuple[str, str], subject_key: str) -> Path:
    root = _tenant_root(tenant)
    temp_dir = Path(tempfile.mkdtemp())
    bundle = temp_dir / "bundle"
    bundle.mkdir()
    copied: Dict[str, str] = {}
    for f in root.rglob("*"):
        if f.is_file():
            try:
                txt = f.read_text()
            except Exception:
                continue
            if subject_key in txt:
                rel = f.relative_to(root)
                dst = bundle / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(txt)
                copied[str(rel)] = str(dst)
    _make_manifest(bundle, copied)
    out_path = temp_dir / "subject_export.zip"
    with zipfile.ZipFile(out_path, "w") as z:
        for f in bundle.rglob("*"):
            z.write(f, f.relative_to(bundle))
    _write_receipt(tenant, "export_subject", {"path": str(out_path)})
    return out_path
