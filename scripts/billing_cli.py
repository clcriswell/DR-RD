#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dr_rd.billing.invoicing import build_invoice, forecast_next_month  # noqa: E402
from dr_rd.billing.quotas import compute_budget  # noqa: E402


def cmd_summarize(args: argparse.Namespace) -> None:
    org, ws = args.tenant.split("/")
    base = Path(args.base) / "tenants" / org / ws / "billing" / f"summary_{args.month}.json"
    data = json.loads(base.read_text()) if base.exists() else {}
    print(json.dumps(data))


def cmd_invoice(args: argparse.Namespace) -> None:
    org, ws = args.tenant.split("/")
    inv = build_invoice(args.month, (org, ws), base_dir=Path(args.out))
    print(json.dumps({"total_usd": inv.total_usd}))


def cmd_forecast(args: argparse.Namespace) -> None:
    org, ws = args.tenant.split("/")
    data = forecast_next_month((org, ws), trailing_days=args.days)
    print(json.dumps(data))


def cmd_quota(args: argparse.Namespace) -> None:
    org, ws = args.tenant.split("/")
    bw = compute_budget(args.month, (org, ws))
    print(json.dumps({"usage": bw.usage, "remaining": bw.remaining}))


def main() -> None:
    parser = argparse.ArgumentParser(description="Billing operations")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sum = sub.add_parser("summarize")
    p_sum.add_argument("--month", required=True)
    p_sum.add_argument("--tenant", required=True)
    p_sum.add_argument("--base", default=".dr_rd")
    p_sum.set_defaults(func=cmd_summarize)

    p_inv = sub.add_parser("invoice")
    p_inv.add_argument("--month", required=True)
    p_inv.add_argument("--tenant", required=True)
    p_inv.add_argument("--out", default=".dr_rd")
    p_inv.set_defaults(func=cmd_invoice)

    p_fore = sub.add_parser("forecast")
    p_fore.add_argument("--tenant", required=True)
    p_fore.add_argument("--days", type=int, default=7)
    p_fore.set_defaults(func=cmd_forecast)

    p_quota = sub.add_parser("quota-status")
    p_quota.add_argument("--month", required=True)
    p_quota.add_argument("--tenant", required=True)
    p_quota.set_defaults(func=cmd_quota)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
