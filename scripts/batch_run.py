from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Mapping, Iterable

from utils.cli import print_summary, load_config
from scripts.run_cli import run as run_single
from utils import telemetry


def _read_items(jsonl: str | None, csv_path: str | None) -> Iterable[Mapping]:
    if jsonl:
        for line in Path(jsonl).read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, Mapping) and "lockfile" in obj:
                yield load_config(None, obj["lockfile"])
            else:
                yield obj
    elif csv_path:
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                cfg = {k: v for k, v in row.items() if v != ""}
                if "budget_limit_usd" in cfg:
                    cfg["budget_limit_usd"] = float(cfg["budget_limit_usd"])
                if "max_tokens" in cfg:
                    cfg["max_tokens"] = int(cfg["max_tokens"])
                yield cfg
    else:
        return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run multiple DR RD pipelines from a list of configs")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--jsonl", help="Path to JSONL file")
    group.add_argument("--csv", help="Path to CSV file")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--deadline-sec", type=float, default=None)
    parser.add_argument("--budget-usd", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--stop-on-fail", action="store_true")
    parser.add_argument("--out-dir", default=".dr_rd/runs")
    parser.add_argument("--no-telemetry", action="store_true")
    args = parser.parse_args(argv)

    telemetry_enabled = not args.no_telemetry
    if telemetry_enabled:
        telemetry.log_event({"event": "batch_started"})

    items = list(_read_items(args.jsonl, args.csv))
    results: list[dict] = []

    def _do(cfg: Mapping):
        b = cfg.get("budget_limit_usd") if "budget_limit_usd" in cfg else args.budget_usd
        mt = cfg.get("max_tokens") if "max_tokens" in cfg else args.max_tokens
        meta, totals = run_single(
            cfg,
            out_dir=args.out_dir,
            deadline_sec=args.deadline_sec,
            telemetry_enabled=telemetry_enabled,
            budget_usd=b,
            max_tokens=mt,
        )
        print_summary(meta, totals)
        return meta

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = [ex.submit(_do, cfg) for cfg in items]
        for fut in as_completed(futures):
            meta = fut.result()
            rid = meta.get("run_id")
            results.append({"run_id": rid, "status": meta.get("status"), "path": str(Path(args.out_dir) / str(rid))})
            if args.stop_on_fail and meta.get("status") == "error":
                for f in futures:
                    f.cancel()
                break

    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    summary = {"runs": results, "counts": counts}
    Path("batch_summary.json").write_text(json.dumps(summary, indent=2))

    if telemetry_enabled:
        telemetry.log_event({"event": "batch_completed", "counts": counts})

    if any(r["status"] == "error" for r in results):
        code = 1
    elif any(r["status"] in {"cancelled", "timeout", "resumable"} for r in results):
        code = 2
    else:
        code = 0
    return code


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
