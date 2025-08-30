#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import argparse
import os

from utils.health_check import run_all, to_markdown


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-net", action="store_true", help="skip network checks")
    args = parser.parse_args()
    if args.no_net:
        os.environ["NO_NET"] = "1"
    report = run_all()
    print(to_markdown(report))
    sys.exit(0 if report.summary.get("fail", 0) == 0 else 1)


if __name__ == "__main__":
    main()
