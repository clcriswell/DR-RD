"""Run comparison helpers.

Provides utilities to load runs, diff configs/metrics, align trace
steps and render a Markdown report.  No Streamlit imports are used so
the module can power both CLI tools and UI pages.
"""

from __future__ import annotations

import difflib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .metrics import ensure_run_totals
from .paths import artifact_path
from .runs import load_run_meta
from .trace_export import flatten_trace_rows


@dataclass(frozen=True)
class AlignedStep:
    a_id: str | None
    b_id: str | None
    a: dict[str, Any] | None
    b: dict[str, Any] | None
    similarity: float  # 0..1 on name/summary


def load_run(run_id: str) -> dict[str, Any]:
    """Load run metadata, lockfile, trace rows and totals.

    Returns a dict with keys ``run_id``, ``meta``, ``lock``,
    ``trace_rows`` and ``totals``.
    """

    meta = load_run_meta(run_id) or {}
    lock_path = artifact_path(run_id, "run_config.lock", "json")
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except Exception:
        lock = {}
    trace_path = artifact_path(run_id, "trace", "json")
    try:
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
    except Exception:
        trace = []
    rows = flatten_trace_rows(trace)
    totals_raw = ensure_run_totals(meta, rows)
    totals = {
        "tokens": int(totals_raw.get("tokens", 0)),
        "cost_usd": float(totals_raw.get("cost_usd", 0.0)),
        "duration_s": float(totals_raw.get("duration_ms", 0.0)) / 1000.0,
    }
    return {
        "run_id": run_id,
        "meta": meta,
        "lock": lock,
        "trace_rows": rows,
        "totals": totals,
    }


def diff_configs(lock_a: dict[str, Any], lock_b: dict[str, Any]) -> list[tuple[str, Any, Any]]:
    """Return list of ``(path, a, b)`` for keys that differ.

    Nested dicts are flattened using dotted paths.  Fields that are
    considered volatile (timestamps or environment hashes) are ignored.
    """

    ignore = {
        "started_at",
        "completed_at",
        "timestamp",
        "ts",
        "env_hash",
        "env_snapshot",
        "env_snapshot_hash",
    }

    def _flatten(d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        items: dict[str, Any] = {}
        for k, v in (d or {}).items():
            if k in ignore:
                continue
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                items.update(_flatten(v, path))
            else:
                items[path] = v
        return items

    flat_a = _flatten(lock_a or {})
    flat_b = _flatten(lock_b or {})
    diffs: list[tuple[str, Any, Any]] = []
    for path in sorted(set(flat_a) | set(flat_b)):
        a_val = flat_a.get(path)
        b_val = flat_b.get(path)
        if a_val != b_val:
            diffs.append((path, a_val, b_val))
    return diffs


def diff_metrics(tot_a: dict[str, Any], tot_b: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Compute deltas between two metric dictionaries."""

    metrics: dict[str, dict[str, float]] = {}
    for key in ("tokens", "cost_usd", "duration_s"):
        a = float(tot_a.get(key, 0.0))
        b = float(tot_b.get(key, 0.0))
        delta = b - a
        pct = delta / a if a else (math.inf if delta else 0.0)
        metrics[key] = {"a": a, "b": b, "delta": delta, "pct": pct}
    return metrics


def _sig(s: str) -> str:
    return s.lower()


def align_steps(rows_a: list[dict], rows_b: list[dict]) -> list[AlignedStep]:
    """Align steps by phase then by fuzzy name similarity.

    A greedy matcher pairs steps within the same phase using
    :class:`difflib.SequenceMatcher`.  Unpaired steps become gaps.
    """

    result: list[AlignedStep] = []
    # Some trace rows may not include a ``phase`` field.  ``sorted()`` cannot
    # compare ``None`` with ``str`` so we normalise the set by excluding
    # ``None`` values and append a ``None`` phase at the end if necessary.
    phase_set = {
        r.get("phase")
        for r in rows_a + rows_b  # type: ignore[operator]
        if r.get("phase") is not None
    }
    phases = sorted(phase_set)
    if any(r.get("phase") is None for r in rows_a + rows_b):  # type: ignore[operator]
        phases.append(None)

    for phase in phases:
        a_phase = [r for r in rows_a if r.get("phase") == phase]
        b_phase = [r for r in rows_b if r.get("phase") == phase]
        used_b: set[int] = set()
        for ra in a_phase:
            sig_a = _sig(ra.get("name") or "")
            best_j = None
            best_score = 0.0
            for j, rb in enumerate(b_phase):
                if j in used_b:
                    continue
                sig_b = _sig(rb.get("name") or "")
                score = difflib.SequenceMatcher(None, sig_a, sig_b).ratio()
                if score > best_score:
                    best_score = score
                    best_j = j
            if best_j is not None and best_score >= 0.5:
                rb = b_phase[best_j]
                used_b.add(best_j)
                result.append(AlignedStep(ra.get("id"), rb.get("id"), ra, rb, best_score))
            else:
                result.append(AlignedStep(ra.get("id"), None, ra, None, 0.0))
        for j, rb in enumerate(b_phase):
            if j not in used_b:
                result.append(AlignedStep(None, rb.get("id"), None, rb, 0.0))
    return result


def diff_steps(a: dict | None, b: dict | None) -> dict[str, Any]:
    """Compare two step dicts."""

    a_dur = float(a.get("duration_ms") or 0 if a else 0)
    b_dur = float(b.get("duration_ms") or 0 if b else 0)
    a_tok = float(a.get("tokens") or 0 if a else 0)
    b_tok = float(b.get("tokens") or 0 if b else 0)
    a_cost = float(a.get("cost") or 0 if a else 0)
    b_cost = float(b.get("cost") or 0 if b else 0)
    sim = 0.0
    if a and b:
        sim = difflib.SequenceMatcher(
            None, _sig(a.get("summary") or ""), _sig(b.get("summary") or "")
        ).ratio()
    return {
        "a_status": a.get("status") if a else None,
        "b_status": b.get("status") if b else None,
        "d_duration_ms": b_dur - a_dur,
        "d_tokens": b_tok - a_tok,
        "d_cost": b_cost - a_cost,
        "summary_ratio": sim,
    }


def to_markdown(
    run_a: dict,
    run_b: dict,
    cfg_diffs: list[tuple[str, Any, Any]],
    met_diffs: dict[str, dict[str, float]],
    aligned: list[AlignedStep],
) -> str:
    """Render a Markdown comparison report."""

    def _ts(meta: dict[str, Any], key: str) -> str:
        ts = meta.get(key)
        if not ts:
            return ""
        try:
            return datetime.fromtimestamp(float(ts)).isoformat()
        except Exception:
            return str(ts)

    lines: list[str] = []
    lines.append(f"# Run Comparison {run_a['run_id']} vs {run_b['run_id']}\n")
    lines.append(
        f"- A started: {_ts(run_a['meta'], 'started_at')}\n- B started: {_ts(run_b['meta'], 'started_at')}\n"
    )
    lines.append("\n## Metrics\n")
    lines.append("|metric|a|b|delta|pct|\n|---|---:|---:|---:|---:|")
    for m, vals in met_diffs.items():
        lines.append(f"|{m}|{vals['a']}|{vals['b']}|{vals['delta']}|{vals['pct']*100:.1f}%|")

    lines.append("\n## Config differences\n")
    if cfg_diffs:
        for path, a, b in cfg_diffs:
            lines.append(f"- `{path}`: `{a}` → `{b}`")
    else:
        lines.append("- None")

    lines.append("\n## Trace steps\n")
    lines.append(
        "|phase|a_name/status|b_name/status|Δdur_ms|Δtokens|Δcost|sim|\n|---|---|---|---:|---:|---:|---:|"
    )
    for step in aligned:
        phase = (step.a or step.b).get("phase") if (step.a or step.b) else ""
        diff = diff_steps(step.a, step.b)
        a_lab = f"{step.a.get('name')} ({diff['a_status']})" if step.a else "—"
        b_lab = f"{step.b.get('name')} ({diff['b_status']})" if step.b else "—"
        lines.append(
            f"|{phase}|{a_lab}|{b_lab}|{diff['d_duration_ms']}|{diff['d_tokens']}|{diff['d_cost']}|{diff['summary_ratio']*100:.1f}%|"
        )

    return "\n".join(lines) + "\n"


__all__ = [
    "AlignedStep",
    "load_run",
    "diff_configs",
    "diff_metrics",
    "align_steps",
    "diff_steps",
    "to_markdown",
]
