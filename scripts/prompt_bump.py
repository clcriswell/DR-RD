#!/usr/bin/env python3
"""Bump prompt version and append changelog."""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import sys
import yaml

from utils.prompts import versioning


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--part", choices=["patch", "minor", "major"], required=True)
    ap.add_argument("path", help="YAML file", nargs="?")
    ns = ap.parse_args()
    path = Path(ns.path or f"prompts/{ns.id}.yaml")
    data = yaml.safe_load(path.read_text())
    if data.get("id") != ns.id:
        print("id mismatch", file=sys.stderr)
        return 1
    new_version = versioning.next_version(data["version"], ns.part)
    data["version"] = new_version
    ts = dt.datetime.utcnow().isoformat()
    data.setdefault("changelog", []).append(f"{new_version}: bumped {ts}")
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
