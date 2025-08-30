"""CLI for comparing two runs and emitting a Markdown diff."""

from __future__ import annotations

import argparse
from pathlib import Path

from utils import compare


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two runs")
    parser.add_argument("--run-a", required=True, help="Run ID A")
    parser.add_argument("--run-b", required=True, help="Run ID B")
    parser.add_argument("--out", help="Output path for Markdown diff")
    args = parser.parse_args()

    run_a = compare.load_run(args.run_a)
    run_b = compare.load_run(args.run_b)
    cfg = compare.diff_configs(run_a["lock"], run_b["lock"])
    mets = compare.diff_metrics(run_a["totals"], run_b["totals"])
    aligned = compare.align_steps(run_a["trace_rows"], run_b["trace_rows"])
    md = compare.to_markdown(run_a, run_b, cfg, mets, aligned)

    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
    else:
        print(md)


if __name__ == "__main__":
    main()

