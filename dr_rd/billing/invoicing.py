from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, Tuple

import yaml

from .models import CostLineItem, Invoice
from .rates import price_model_call, price_tools

CFG_PATH = Path("config/billing.yaml")


def _cfg() -> Dict:
    with CFG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _round(amount: float, cents: int) -> float:
    return round(amount, cents)


def build_invoice(period_ym: str, tenant_key: Tuple[str, str], base_dir: Path | str = Path(".dr_rd")) -> Invoice:
    org, ws = tenant_key
    cfg = _cfg()
    billing = cfg.get("billing", {})
    base = Path(base_dir) / "tenants" / org / ws / "billing"
    summary_path = base / f"summary_{period_ym}.json"
    summary = json.loads(summary_path.read_text())
    usage = summary.get("monthly", {})

    free = billing.get("free_tier", {})
    bill_tokens_in = max(0, usage.get("tokens_in", 0) - free.get("monthly_tokens_in", 0))
    bill_tokens_out = max(0, usage.get("tokens_out", 0) - free.get("monthly_tokens_out", 0))
    bill_tool_calls = max(0, usage.get("tool_calls", 0) - free.get("monthly_tool_calls", 0))
    bill_tool_runtime = max(0, usage.get("tool_runtime_ms", 0) - free.get("monthly_tool_runtime_ms", 0))

    li_model = price_model_call(bill_tokens_in, bill_tokens_out, provider="openai", model="gpt-4.1-mini")
    li_model.org_id = org
    li_model.workspace_id = ws
    li_model.period = period_ym

    li_tools = price_tools(bill_tool_calls, bill_tool_runtime)
    li_tools.org_id = org
    li_tools.workspace_id = ws
    li_tools.period = period_ym

    line_items = [li_model, li_tools]
    subtotal = sum(li.amount_usd for li in line_items)
    tax_rate = billing.get("taxes", {}).get("rate", 0.0)
    tax = subtotal * tax_rate
    total = subtotal + tax
    cents = billing.get("rounding", {}).get("cents", 2)
    subtotal = _round(subtotal, cents)
    tax = _round(tax, cents)
    total = _round(total, cents)

    invoice = Invoice(
        invoice_id=f"{org}-{ws}-{period_ym}",
        org_id=org,
        workspace_id=ws,
        period=period_ym,
        line_items=line_items,
        subtotal_usd=subtotal,
        tax_usd=tax,
        total_usd=total,
        usage_summary=usage,
    )

    # Emit files
    json_path = base / f"invoice_{period_ym}.json"
    csv_path = base / f"invoice_{period_ym}.csv"
    html_path = base / f"invoice_{period_ym}.html"
    json_path.write_text(json.dumps(invoice, default=lambda o: o.__dict__, indent=2))
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["kind", "quantity", "unit_price", "amount"])
        for li in line_items:
            writer.writerow([li.kind, li.quantity, li.unit_price_usd, li.amount_usd])
        writer.writerow(["subtotal", "", "", subtotal])
        writer.writerow(["tax", "", "", tax])
        writer.writerow(["total", "", "", total])
    html_path.write_text(
        "<html><body><h1>Invoice {}</h1><p>Total: ${:.2f}</p></body></html>".format(
            invoice.invoice_id, total
        )
    )
    return invoice


def forecast_next_month(tenant_key: Tuple[str, str], trailing_days: int = 7, base_dir: Path | str = Path(".dr_rd")) -> Dict[str, float]:
    org, ws = tenant_key
    today = date.today()
    start = today - timedelta(days=trailing_days)
    events = []
    # For simplicity, load current month summary and extrapolate
    period = today.strftime("%Y-%m")
    base = Path(base_dir) / "tenants" / org / ws / "billing"
    summary_path = base / f"summary_{period}.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())
        usage = summary.get("monthly", {})
        days_in_month = (date(today.year + int(today.month / 12), ((today.month % 12) + 1), 1) - date(today.year, today.month, 1)).days
        factor = days_in_month / max(1, (today - date(today.year, today.month, 1)).days)
        forecast = {k: v * factor for k, v in usage.items()}
    else:
        forecast = {}
    return forecast


__all__ = ["build_invoice", "forecast_next_month"]
