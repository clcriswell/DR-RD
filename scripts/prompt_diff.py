#!/usr/bin/env python3
"""Show diff between prompt versions."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
import sys

import yaml
from utils.prompts import versioning


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--new_path", default=None)
    ns = ap.parse_args()
    path = Path(ns.new_path or f"prompts/{ns.id}.yaml")
    new_text = path.read_text()
    try:
        old_yaml = subprocess.check_output(
            ["git", "show", f"{ns.old}:prompts/{ns.id}.yaml"], text=True
        )
    except Exception:
        print("old version not found", file=sys.stderr)
        return 1
    diff = versioning.unified_diff(old_yaml, new_text)
    sys.stdout.write(diff)
    return 0


if __name__ == "__main__":
    sys.exit(main())
