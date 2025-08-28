#!/usr/bin/env python
"""Validate configuration lock file matches current config."""

from __future__ import annotations

import json
import os
import sys

from freeze_config import LOCK_FILE, compute_snapshot


def main() -> None:
    allow = os.getenv("ALLOW_CONFIG_DRIFT") == "1"
    if not LOCK_FILE.exists():
        print("config lock missing", file=sys.stderr)
        sys.exit(1)
    with LOCK_FILE.open("r", encoding="utf-8") as f:
        recorded = json.load(f)
    current = compute_snapshot()
    if recorded.get("sha256") != current.get("sha256"):
        if allow:
            print("config drift detected but allowed", file=sys.stderr)
        else:
            print("config drift detected", file=sys.stderr)
            sys.exit(1)
    else:
        print("config lock validated")


if __name__ == "__main__":
    main()
