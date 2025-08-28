#!/usr/bin/env python
"""Generate a deterministic snapshot of configuration files."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import yaml

CONFIG_DIR = Path("config")
LOCK_FILE = CONFIG_DIR / "config.lock.json"


def _load_feature_flags() -> dict:
    spec = importlib.util.spec_from_file_location("feature_flags", CONFIG_DIR / "feature_flags.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return {k: getattr(module, k) for k in dir(module) if k.isupper()}


def _sanitize(obj):
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(x) for x in obj]
    if isinstance(obj, Path):
        return str(obj)
    return obj


def compute_snapshot() -> dict:
    data: dict[str, object] = {}
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as f:
            data[path.name] = _sanitize(yaml.safe_load(f) or {})
    data["feature_flags.py"] = _sanitize(_load_feature_flags())
    normalized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    sha = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return {"sha256": sha, "config": data}


def main() -> None:
    snapshot = compute_snapshot()
    with LOCK_FILE.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
