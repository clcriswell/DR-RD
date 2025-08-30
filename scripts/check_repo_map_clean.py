#!/usr/bin/env python3
"""Verify repo_map.yaml and docs/REPO_MAP.md are up to date."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from scripts.generate_repo_map import build_repo_map, render_repo_map_doc  # noqa: E402


def main() -> int:
    current_yaml = yaml.safe_load((ROOT / "repo_map.yaml").read_text())
    data = build_repo_map()
    data["generated_at"] = current_yaml.get("generated_at")
    if current_yaml != data:
        print("repo_map.yaml is stale. Run scripts/generate_repo_map.py")
        return 1
    rendered = render_repo_map_doc(data)
    current_doc = (ROOT / "docs" / "REPO_MAP.md").read_text()
    if current_doc.strip() != rendered.strip():
        print("docs/REPO_MAP.md is stale. Run scripts/generate_repo_map.py")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
