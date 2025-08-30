from __future__ import annotations

"""Headless evaluation runner CLI."""

import argparse
import sys
from pathlib import Path

from utils.eval import datasets, runner


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--use-llm", action="store_true")
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--out")
    args = ap.parse_args()

    path = Path(args.dataset)
    if path.suffix == ".jsonl":
        items = datasets.normalize(datasets.load_jsonl(str(path)))
    else:
        items = datasets.normalize(datasets.load_csv(str(path)))
    summary = runner.run_eval(items, use_llm=args.use_llm, concurrency=args.concurrency, out_dir=args.out)
    print(
        f"Ran {len(items)} items: pass_rate={summary['pass_rate']:.2f} mean_final={summary['mean_final']:.2f}"
    )
    ok = all(r["status"] == "success" for r in summary["rows"]) and summary["pass_rate"] >= 0.7
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
