from __future__ import annotations

import argparse
import shutil
from pathlib import Path

RUNS_ROOT = Path(".dr_rd") / "runs"


def _run_dirs():
    if not RUNS_ROOT.exists():
        return []
    return sorted([p for p in RUNS_ROOT.iterdir() if p.is_dir()])


def cleanup_keep(keep: int) -> None:
    dirs = _run_dirs()
    for p in dirs[:-keep]:
        shutil.rmtree(p, ignore_errors=True)
        print(f"Deleted {p}")


def cleanup_max_bytes(limit: int) -> None:
    dirs = _run_dirs()
    sizes = [(p, sum(f.stat().st_size for f in p.rglob("*") if f.is_file())) for p in dirs]
    total = sum(s for _, s in sizes)
    for p, s in sizes:
        if total <= limit:
            break
        shutil.rmtree(p, ignore_errors=True)
        total -= s
        print(f"Deleted {p}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cleanup old run artifacts")
    parser.add_argument("--keep", type=int, help="Keep newest N runs")
    parser.add_argument("--max-bytes", type=int, dest="max_bytes", help="Max total bytes to keep")
    args = parser.parse_args()
    if args.keep is not None:
        cleanup_keep(args.keep)
    elif args.max_bytes is not None:
        cleanup_max_bytes(args.max_bytes)
    else:
        parser.error("Specify --keep or --max-bytes")


if __name__ == "__main__":
    main()
