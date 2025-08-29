from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from .models import UsageEvent


def _parse_line(data: dict) -> UsageEvent:
    ts = datetime.fromisoformat(data["ts"])
    return UsageEvent(
        ts=ts,
        org_id=data.get("org_id", "default"),
        workspace_id=data.get("workspace_id", "default"),
        run_id=data.get("run_id", ""),
        phase=data.get("phase", ""),
        agent=data.get("agent"),
        provider=data.get("provider"),
        model=data.get("model"),
        tokens_in=int(data.get("tokens_in", 0)),
        tokens_out=int(data.get("tokens_out", 0)),
        tool_calls=int(data.get("tool_calls", 0)),
        tool_runtime_ms=int(data.get("tool_runtime_ms", 0)),
        retrieval_docs=int(data.get("retrieval_docs", 0)),
        cache_bytes=int(data.get("cache_bytes", 0)),
        meta=data.get("meta", {}),
    )


def collect_usage(log_paths: Sequence[Path | str]) -> List[UsageEvent]:
    """Collect UsageEvents from telemetry/provenance logs.

    Parameters
    ----------
    log_paths: list of file paths containing JSON lines.
    """

    events: List[UsageEvent] = []
    for path in log_paths:
        p = Path(path)
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                data = json.loads(line)
                events.append(_parse_line(data))
    return events


def aggregate_month(events: Iterable[UsageEvent]) -> Dict[Tuple[str, str], Dict[str, Dict[str, int]]]:
    """Aggregate UsageEvents into monthly and daily rollups."""
    result: Dict[Tuple[str, str], Dict[str, Dict[str, int]]] = {}
    daily: Dict[Tuple[str, str], Dict[str, Dict[str, int]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    monthly: Dict[Tuple[str, str], Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for ev in events:
        key = (ev.org_id, ev.workspace_id)
        day = ev.ts.strftime("%Y-%m-%d")
        metrics = {
            "tokens_in": ev.tokens_in,
            "tokens_out": ev.tokens_out,
            "tool_calls": ev.tool_calls,
            "tool_runtime_ms": ev.tool_runtime_ms,
        }
        for k, v in metrics.items():
            daily[key][day][k] += v
            monthly[key][k] += v

    for key in monthly:
        result[key] = {
            "monthly": dict(monthly[key]),
            "daily": {d: dict(vals) for d, vals in daily[key].items()},
        }
    return result


def persist_monthly_usage(
    tenant_key: Tuple[str, str],
    period: str,
    events: Iterable[UsageEvent],
    base_dir: Path | str = Path(".dr_rd"),
) -> None:
    """Persist usage events and monthly summary for a tenant."""
    org, ws = tenant_key
    base = Path(base_dir) / "tenants" / org / ws / "billing"
    base.mkdir(parents=True, exist_ok=True)
    usage_path = base / f"usage_{period}.jsonl"
    summary_path = base / f"summary_{period}.json"

    with usage_path.open("w", encoding="utf-8") as fh:
        for ev in events:
            fh.write(
                json.dumps(
                    {
                        "ts": ev.ts.isoformat(),
                        "org_id": ev.org_id,
                        "workspace_id": ev.workspace_id,
                        "run_id": ev.run_id,
                        "phase": ev.phase,
                        "tokens_in": ev.tokens_in,
                        "tokens_out": ev.tokens_out,
                        "tool_calls": ev.tool_calls,
                        "tool_runtime_ms": ev.tool_runtime_ms,
                    }
                )
                + "\n"
            )

    agg = aggregate_month(events)[tenant_key]
    with summary_path.open("w", encoding="utf-8") as fh:
        json.dump(agg, fh, indent=2, sort_keys=True)


__all__ = ["collect_usage", "aggregate_month", "persist_monthly_usage"]
