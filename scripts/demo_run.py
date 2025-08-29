from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path

from scripts.demos import flows


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow", choices=list(flows.FLOW_MAP) + ["all"], required=True)
    parser.add_argument("--out", default=None, help="Output directory")
    parser.add_argument("--flags", default=None, help="Comma separated KEY=VAL")
    args = parser.parse_args(argv)

    out_dir = args.out
    if out_dir is None:
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_dir = f"samples/runs/{stamp}"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    if args.flow == "all":
        flows.run_all(out_dir, args.flags)
    else:
        flows.FLOW_MAP[args.flow](out_dir, args.flags)

    print(f"Artifacts written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
