from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Mapping, Sequence

from .cache import cached_data
from .diff_runs import aggregate_from_rows
from .lazy_import import lazy

EVENTS_PATH = Path(".dr_rd/telemetry/events.jsonl")
SURVEYS_PATH = Path(".dr_rd/telemetry/surveys.jsonl")
ARTIFACTS_DIR = Path(".dr_rd/artifacts")

_pd = lazy("pandas")


@cached_data(ttl=15)
def load_events(limit: int = 10000) -> list[dict]:
    if not EVENTS_PATH.exists():
        return []
    with EVENTS_PATH.open("r", encoding="utf-8") as f:
        lines = f.readlines()[-limit:]
    return [json.loads(line) for line in lines]


@cached_data(ttl=15)
def load_surveys(limit: int = 2000) -> list[dict]:
    if not SURVEYS_PATH.exists():
        return []
    with SURVEYS_PATH.open("r", encoding="utf-8") as f:
        lines = f.readlines()[-limit:]
    return [json.loads(line) for line in lines]


def last_run_id(events: list[dict]) -> str | None:
    for ev in reversed(events):
        if ev.get("event") == "start_run":
            return ev.get("run_id")
    return None


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def compute_aggregates(events: list[dict], surveys: list[dict]) -> dict[str, float]:
    now = time.time()
    cutoff = now - 7 * 24 * 60 * 60

    runs = [e for e in events if e.get("event") == "start_run"]
    views = [e for e in events if e.get("event") == "nav_page_view"]
    errors = [e for e in events if e.get("event") == "error_shown"]
    completes = [e for e in events if e.get("event") == "run_complete"]
    successes = [e for e in completes if e.get("success", True)]
    failures = [e for e in completes if not e.get("success", True)]
    durations = [
        e.get("duration_s", 0) for e in completes if isinstance(e.get("duration_s"), (int, float))
    ]

    sus_scores = [r.get("total", 0) for r in surveys if r.get("instrument") == "SUS"]
    sus_recent = [
        r.get("total", 0)
        for r in surveys
        if r.get("instrument") == "SUS" and r.get("ts", 0) >= cutoff
    ]
    seq_scores = [
        r.get("answers", {}).get("score") for r in surveys if r.get("instrument") == "SEQ"
    ]
    seq_recent = [
        r.get("answers", {}).get("score")
        for r in surveys
        if r.get("instrument") == "SEQ" and r.get("ts", 0) >= cutoff
    ]

    return {
        "runs": len(runs),
        "views": len(views),
        "errors": len(errors),
        "error_rate": len(errors) / len(runs) if runs else 0.0,
        "success_rate": (
            len(successes) / (len(successes) + len(failures)) if (successes or failures) else 0.0
        ),
        "avg_time_on_task": _mean(durations),
        "sus_count": len(sus_scores),
        "sus_mean": _mean([s for s in sus_scores if s is not None]),
        "sus_7_day_mean": _mean([s for s in sus_recent if s is not None]),
        "seq_count": len([s for s in seq_scores if s is not None]),
        "seq_mean": _mean([s for s in seq_scores if s is not None]),
        "seq_7_day_mean": _mean([s for s in seq_recent if s is not None]),
    }


@cached_data(ttl=5)
def list_artifacts(run_id: str | None = None) -> dict[str, str]:
    base = ARTIFACTS_DIR / run_id if run_id else ARTIFACTS_DIR
    if not base.exists():
        return {}
    return {p.name: str(p) for p in base.glob("**/*") if p.is_file()}


def ensure_run_totals(
    meta: Mapping[str, float] | None, rows: Sequence[Mapping[str, object]]
) -> dict[str, float]:
    """Return per-run totals, computing from ``rows`` if ``meta`` lacks values."""
    totals: dict[str, float] = {}
    if meta:
        for key in ("steps", "errors", "duration_ms", "tokens", "cost_usd"):
            if key in meta:
                try:
                    totals[key] = float(meta[key])
                except (TypeError, ValueError):
                    continue
    if len(totals) < 5:
        computed = aggregate_from_rows(rows)
        for key, val in computed.items():
            totals.setdefault(key, val)
    return totals


def to_table(rows: Sequence[Mapping[str, object]]):
    """Return rows as a :class:`pandas.DataFrame` using lazy import."""
    return _pd.DataFrame(list(rows))
