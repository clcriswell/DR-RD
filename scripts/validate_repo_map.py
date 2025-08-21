#!/usr/bin/env python3
"""Validate repo_map.yaml and generated docs are up to date and consistent."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.append(str(Path(__file__).parent))
from generate_repo_map import (  # noqa: E402
    DOC_PATH,
    YAML_PATH,
    build_repo_map,
    render_repo_map_doc,
)


def _compare_dicts(a: dict, b: dict) -> bool:
    return yaml.safe_dump(a, sort_keys=True) == yaml.safe_dump(b, sort_keys=True)


def main() -> None:
    current = yaml.safe_load(YAML_PATH.read_text())
    regenerated = build_repo_map()
    cur_cmp = dict(current)
    regen_cmp = dict(regenerated)
    for d in (cur_cmp, regen_cmp):
        d.pop("generated_at", None)
        d.pop("git_sha", None)
    if not _compare_dicts(cur_cmp, regen_cmp):
        print("repo_map.yaml is out of date. Run make repo-map and commit updates.")
        sys.exit(1)
    rendered = render_repo_map_doc(current)
    if DOC_PATH.read_text() != rendered:
        print("docs/REPO_MAP.md is out of date. Run make repo-map and commit updates.")
        sys.exit(1)

    modes = yaml.safe_load(Path("config/modes.yaml").read_text())
    prices = yaml.safe_load(Path("config/prices.yaml").read_text())
    for key in ["test", "deep"]:
        if key not in modes or "target_cost_usd" not in modes[key]:
            print(f"config/modes.yaml missing {key}.target_cost_usd")
            sys.exit(1)
    if "models" not in prices:
        print("config/prices.yaml missing 'models' key")
        sys.exit(1)

    roles = current.get("agent_registry", {})
    if len(roles) != len(set(roles)):
        print("Duplicate agent roles detected")
        sys.exit(1)

    print("Repo map validation passed.")


if __name__ == "__main__":
    main()
