"""Schedule the planning → execution → reporting cycle."""
from __future__ import annotations

import argparse
import py_compile
import sched
import sys
import time
from pathlib import Path

if __package__ is None or __package__ == "":  # allow running as script
    sys.path.append(str(Path(__file__).resolve().parent.parent))
from scripts.generate_dev_report import main as generate_report


def obfuscate_source(src: Path, out: Path) -> None:
    """Compile Python sources to bytecode in *out*.

    This provides a lightweight form of obfuscation by distributing
    `.pyc` files instead of raw `.py` sources.
    """
    for py in src.rglob("*.py"):
        rel = py.relative_to(src)
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        py_compile.compile(str(py), cfile=str(target.with_suffix(".pyc")), optimize=2)


def run_cycle(obfuscate: bool) -> None:
    """Run one full planning → execution → reporting cycle."""
    generate_report()
    if obfuscate:
        out_dir = Path("build/obfuscated")
        obfuscate_source(Path("src"), out_dir)
        print(f"Obfuscated bytecode written to {out_dir}")


def schedule(interval: int, obfuscate: bool) -> None:
    """Repeatedly run the cycle at *interval* seconds."""
    scheduler = sched.scheduler(time.time, time.sleep)

    def task() -> None:
        run_cycle(obfuscate)
        scheduler.enter(interval, 1, task)

    scheduler.enter(0, 1, task)
    scheduler.run()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--interval", type=int, default=0,
        help="Seconds between cycles; 0 runs once and exits.")
    parser.add_argument(
        "--obfuscate", action="store_true",
        help="Compile sources to bytecode after reporting.")
    return parser.parse_args()


def main() -> None:  # pragma: no cover - manual execution
    args = parse_args()
    if args.interval > 0:
        schedule(args.interval, args.obfuscate)
    else:
        run_cycle(args.obfuscate)


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    main()
