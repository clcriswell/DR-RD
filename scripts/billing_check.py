#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dr_rd.billing.quotas import compute_budget  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Check tenant quota status")
    parser.add_argument("--tenant", required=True, help="org/ws")
    args = parser.parse_args()

    period = date.today().strftime("%Y-%m")
    org, ws = args.tenant.split("/")
    bw = compute_budget(period, (org, ws))
    breached = [k for k, v in bw.remaining.items() if v < 0]
    if breached:
        print(json.dumps({"tenant": args.tenant, "breached": breached}))
        sys.exit(1)
    print(json.dumps({"tenant": args.tenant, "ok": True}))


if __name__ == "__main__":
    main()
