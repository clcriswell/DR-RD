#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dr_rd.billing.invoicing import build_invoice  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate invoices for tenants")
    parser.add_argument("--month", required=True, help="YYYY-MM period")
    parser.add_argument("--tenant", required=True, help="org/ws")
    parser.add_argument("--out", default=".dr_rd", help="output base directory")
    args = parser.parse_args()

    org, ws = args.tenant.split("/")
    inv = build_invoice(args.month, (org, ws), base_dir=Path(args.out))
    print(json.dumps({"tenant": args.tenant, "total_usd": inv.total_usd}))


if __name__ == "__main__":
    main()
