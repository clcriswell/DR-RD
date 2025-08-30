#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))


"""CLI for purging telemetry event logs."""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from utils import telemetry


def _parse_day(p: Path) -> datetime.date:
    name = p.name
    for token in name.split("."):
        if token.startswith("events-"):
            token = token[len("events-") :]
        if token[:8].isdigit():
            try:
                return datetime.strptime(token[:8], "%Y%m%d").date()
            except ValueError:
                pass
    return datetime.utcfromtimestamp(0).date()


def main() -> int:
    ap = argparse.ArgumentParser(description="Purge telemetry logs")
    ap.add_argument("--older-than", type=int, default=None, help="Delete files older than DAYS")
    ap.add_argument("--keep-last-days", type=int, default=None, help="Keep only last N days of logs")
    ap.add_argument("--delete-run", dest="delete_run", help="Remove events for a specific run_id")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without making changes")
    args = ap.parse_args()

    files = telemetry.list_files()
    now = datetime.utcnow().date()
    to_delete: list[Path] = []

    if args.older_than is not None:
        cutoff = now - timedelta(days=args.older_than)
        to_delete.extend([p for p in files if _parse_day(p) < cutoff])

    if args.keep_last_days is not None:
        cutoff = now - timedelta(days=args.keep_last_days)
        to_delete.extend([p for p in files if _parse_day(p) < cutoff and p not in to_delete])

    deleted_bytes = 0
    rewritten = []

    # Delete whole files
    for p in to_delete:
        try:
            deleted_bytes += p.stat().st_size
        except OSError:
            pass
        if args.dry_run:
            print(f"Would delete {p}")
        else:
            try:
                p.unlink()
            except OSError:
                pass

    # Delete specific run_id occurrences
    if args.delete_run:
        rid = args.delete_run
        for p in telemetry.list_files():
            try:
                lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            new_lines = []
            removed = 0
            for line in lines:
                try:
                    ev = json.loads(line)
                except Exception:
                    ev = None
                if ev and ev.get("run_id") == rid:
                    removed += len(line.encode("utf-8"))
                    continue
                new_lines.append(line)
            if removed:
                rewritten.append(p)
                deleted_bytes += removed
                if args.dry_run:
                    print(f"Would rewrite {p} excluding run_id={rid}")
                else:
                    tmp = p.with_suffix(p.suffix + ".tmp")
                    tmp.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                    tmp.replace(p)

    print(
        f"deleted_files={len(to_delete)} rewritten_files={len(rewritten)} freed_bytes={deleted_bytes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
