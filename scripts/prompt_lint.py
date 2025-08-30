#!/usr/bin/env python3
"""Validate prompt registry files."""
from __future__ import annotations

import sys
from utils.prompts import loader


def main() -> int:
    try:
        loader.load_all()
    except Exception as exc:
        print(exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
