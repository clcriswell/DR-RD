#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))


"""Export telemetry events to CSV or Parquet with simple rollups."""

import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from utils.telemetry import read_events

try:  # optional dependency
    import pyarrow as pa
    import pyarrow.parquet as pq
    HAS_PARQUET = True
except Exception:  # pragma: no cover
    HAS_PARQUET = False


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Export telemetry events")
    grp = ap.add_mutually_exclusive_group(required=False)
    grp.add_argument("--days", type=int, help="Number of days back to include")
    grp.add_argument("--from", dest="from_", help="Start date YYYY-MM-DD")
    ap.add_argument("--to", dest="to", help="End date YYYY-MM-DD")
    ap.add_argument("--out", required=True, help="Output file path (.csv or .parquet)")
    ap.add_argument("--rollup", choices=["usage", "runs"], help="Optional rollup")
    return ap.parse_args()


def _filter_range(events: List[Dict[str, Any]], start: datetime, end: datetime) -> List[Dict[str, Any]]:
    return [e for e in events if start.timestamp() <= e.get("ts", 0) < end.timestamp()]


def _rollup_usage(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    per_run: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        rid = ev.get("run_id")
        if not rid:
            continue
        stats = per_run.setdefault(rid, {"tokens": 0, "cost_usd": 0.0, "errors": 0, "start": None, "end": None})
        if ev.get("event") == "start_run":
            stats["start"] = ev.get("ts")
        if ev.get("event") == "run_completed":
            stats["end"] = ev.get("ts")
        if ev.get("event") == "error_shown":
            stats["errors"] += 1
        if "total_tokens" in ev:
            try:
                stats["tokens"] += int(ev["total_tokens"])
            except Exception:
                pass
        if "cost_usd" in ev:
            try:
                stats["cost_usd"] += float(ev["cost_usd"])
            except Exception:
                pass
    rows: List[Dict[str, Any]] = []
    for rid, s in per_run.items():
        duration = None
        if s["start"] and s["end"]:
            duration = s["end"] - s["start"]
        rows.append({"run_id": rid, "tokens": s["tokens"], "cost_usd": round(s["cost_usd"], 6),
                      "duration": duration, "error_count": s["errors"]})
    return rows


def _rollup_runs(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    per_day: Dict[str, Dict[str, Any]] = {}
    starts: Dict[str, float] = {}
    for ev in events:
        if ev.get("event") == "start_run" and ev.get("run_id"):
            starts[ev["run_id"]] = ev.get("ts", 0)
        if ev.get("event") == "run_completed" and ev.get("run_id"):
            ts = ev.get("ts", 0)
            day = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
            d = per_day.setdefault(day, {"success": 0, "error": 0, "cancelled": 0, "timeout": 0, "durations": []})
            status = ev.get("status", "unknown")
            d[status] = d.get(status, 0) + 1
            start_ts = starts.get(ev["run_id"])
            if start_ts:
                d["durations"].append(ts - start_ts)
    rows: List[Dict[str, Any]] = []
    for day, d in sorted(per_day.items()):
        mean_dur = sum(d["durations"]) / len(d["durations"]) if d["durations"] else None
        rows.append({"day": day, "success": d.get("success", 0), "error": d.get("error", 0),
                     "cancelled": d.get("cancelled", 0), "timeout": d.get("timeout", 0),
                     "mean_duration": mean_dur})
    return rows


def main() -> int:
    args = _parse_args()
    if args.from_ and args.to:
        start = datetime.strptime(args.from_, "%Y-%m-%d")
        end = datetime.strptime(args.to, "%Y-%m-%d") + timedelta(days=1)
        days = (datetime.utcnow() - start).days + 1
        events = read_events(days=days)
        events = _filter_range(events, start, end)
    else:
        events = read_events(days=args.days or 7)

    if args.rollup == "usage":
        rows = _rollup_usage(events)
    elif args.rollup == "runs":
        rows = _rollup_runs(events)
    else:
        rows = events

    out = Path(args.out)
    if out.suffix == ".parquet":
        if not HAS_PARQUET:
            raise SystemExit("pyarrow not available")
        table = pa.Table.from_pylist(rows)
        pq.write_table(table, out)
    else:
        fieldnames = sorted({k for r in rows for k in r.keys()}) if rows else []
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)


if __name__ == "__main__":
    raise SystemExit(main())
