#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))


"""CLI for purging telemetry event logs."""

import argparse
from utils import retention


def main() -> int:
    ap = argparse.ArgumentParser(description="Purge telemetry logs")
    ap.add_argument("--older-than", type=int, default=None, help="Delete files older than DAYS")
    ap.add_argument("--keep-last-days", type=int, default=None, help="Keep only last N days of logs")
    ap.add_argument("--delete-run", dest="delete_run", help="Remove events for a specific run_id")
    args = ap.parse_args()
    days = args.keep_last_days if args.keep_last_days is not None else args.older_than
    deleted_files = 0
    rewritten = 0
    if days is not None:
        deleted_files = retention.purge_telemetry_older_than(days)
    if args.delete_run:
        rewritten = retention.delete_run_events(args.delete_run)
    print(f"deleted_files={deleted_files} rewritten_files={rewritten}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
