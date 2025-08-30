#!/usr/bin/env python3
"""Profile import times from ``-X importtime`` logs."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def parse_importtime(path: Path) -> dict[str, float]:
    """Return mapping of module -> cumulative milliseconds."""
    totals: dict[str, float] = {}
    for line in path.read_text().splitlines():
        if not line.startswith("import time:"):
            continue
        if "[us]" in line:  # header
            continue
        parts = line.split("|")
        if len(parts) < 3:
            continue
        try:
            cumulative_us = float(parts[1].strip())
            module = parts[2].strip()
        except ValueError:
            continue
        totals[module] = cumulative_us / 1000.0
    return totals


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path, help="log file from -X importtime")
    ap.add_argument("--top", type=int, default=10, help="rows to display")
    args = ap.parse_args(argv)

    totals = parse_importtime(args.log)
    if not totals:
        print("No import timings found", file=sys.stderr)
        return 1

    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    print(f"Top {args.top} imports by cumulative ms:")
    for mod, ms in top[: args.top]:
        print(f"{mod:40s} {ms:8.1f} ms")

    single_budget = int(os.getenv("IMPORT_BUDGET_SINGLE_MS", "200"))
    total_budget = int(os.getenv("IMPORT_BUDGET_TOTAL_MS", "1200"))

    max_ms = max(totals.values())
    top10_total = sum(ms for _, ms in top[:10])

    if max_ms > single_budget:
        print(f"\nFAIL: module over budget ({max_ms:.1f}ms > {single_budget}ms)")
        return 1
    if top10_total > total_budget:
        print(f"\nFAIL: top10 total {top10_total:.1f}ms exceeds {total_budget}ms")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
