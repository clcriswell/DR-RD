#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from dr_rd.reporting import compose
from dr_rd.reporting.exporters import to_markdown, to_html


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a report from artifacts")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--agents", required=True)
    ap.add_argument("--synth", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.plan, "r", encoding="utf-8") as fh:
        plan = json.load(fh)
    with open(args.synth, "r", encoding="utf-8") as fh:
        synth = json.load(fh)
    agents = []
    with open(args.agents, "r", encoding="utf-8") as fh:
        for line in fh:
            agents.append(json.loads(line))
    report = compose(plan, {"agents": agents, "synth": synth})
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "report.md").write_text(to_markdown(report), encoding="utf-8")
    (out_dir / "report.html").write_text(to_html(report), encoding="utf-8")
    print(f"sources: {len(report.get('sources', []))}")


if __name__ == "__main__":
    main()
