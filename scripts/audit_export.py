from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Export audit log to CSV")
    p.add_argument("path")
    p.add_argument("--out", required=True)
    args = p.parse_args(argv)
    path = Path(args.path)
    out = Path(args.out)
    fieldnames = ["ts", "actor", "action", "resource", "outcome"]
    with path.open() as src, out.open("w", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()
        for line in src:
            rec = json.loads(line)
            writer.writerow({k: rec.get(k) for k in fieldnames})


if __name__ == "__main__":
    main()
