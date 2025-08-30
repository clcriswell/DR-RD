from __future__ import annotations

import csv
import io
import difflib
from typing import Dict, List, Mapping, Sequence, Tuple, Optional

TraceRow = Mapping[str, object]


def aggregate_from_rows(rows: Sequence[TraceRow]) -> Dict[str, float]:
    """Return totals: {'steps':N, 'errors':N, 'duration_ms':sum, 'tokens':sum, 'cost_usd':sum}."""
    steps = len(rows)
    errors = sum(1 for r in rows if r.get("status") == "error")
    duration = sum(float(r.get("duration_ms") or 0) for r in rows)
    tokens = sum(float(r.get("tokens") or 0) for r in rows)
    cost = sum(float(r.get("cost") or 0) for r in rows)
    return {
        "steps": float(steps),
        "errors": float(errors),
        "duration_ms": float(duration),
        "tokens": float(tokens),
        "cost_usd": float(cost),
    }


def align_steps(a: Sequence[TraceRow], b: Sequence[TraceRow]) -> List[Tuple[Optional[TraceRow], Optional[TraceRow], float]]:
    """
    Align by (phase, name) first; if multiple, use order.
    Fallback: fuzzy ratio on 'name' via difflib.SequenceMatcher.
    Return list of tuples (row_a, row_b, score) where None denotes an insert/delete.
    """
    def key(r: TraceRow) -> Tuple[object, object]:
        return (r.get("phase"), r.get("name"))

    b_keys: Dict[Tuple[object, object], List[Tuple[int, TraceRow]]] = {}
    for idx, row in enumerate(b):
        b_keys.setdefault(key(row), []).append((idx, row))

    matched: List[Tuple[int, int, TraceRow, TraceRow, float]] = []
    unmatched_a: List[Tuple[int, TraceRow]] = []
    used_b: set[int] = set()

    for idx_a, row_a in enumerate(a):
        k = key(row_a)
        lst = b_keys.get(k)
        if lst:
            idx_b, row_b = lst.pop(0)
            used_b.add(idx_b)
            matched.append((idx_a, idx_b, row_a, row_b, 1.0))
        else:
            unmatched_a.append((idx_a, row_a))

    unmatched_b: List[Tuple[int, TraceRow]] = [
        (idx, row) for idx, row in enumerate(b) if idx not in used_b
    ]

    # Fuzzy match remaining rows by name
    paired: set[int] = set()
    for ia, row_a in list(unmatched_a):
        candidates = [
            (ib, rb) for ib, rb in unmatched_b if rb.get("phase") == row_a.get("phase")
        ]
        if not candidates:
            candidates = unmatched_b
        best_idx = -1
        best_score = 0.0
        best_row: Optional[TraceRow] = None
        for ib, row_b in candidates:
            if ib in paired:
                continue
            score = difflib.SequenceMatcher(
                None, str(row_a.get("name")), str(row_b.get("name"))
            ).ratio()
            if score > best_score:
                best_score = score
                best_idx = ib
                best_row = row_b
        if best_idx != -1:
            matched.append((ia, best_idx, row_a, best_row, best_score))
            paired.add(best_idx)
            unmatched_a.remove((ia, row_a))
    unmatched_b = [(ib, rb) for ib, rb in unmatched_b if ib not in paired]

    combined: List[Tuple[Optional[int], Optional[int], Optional[TraceRow], Optional[TraceRow], float]] = []
    combined.extend(matched)
    combined.extend((ia, None, ra, None, 0.0) for ia, ra in unmatched_a)
    combined.extend((None, ib, None, rb, 0.0) for ib, rb in unmatched_b)

    def sort_key(item: Tuple[Optional[int], Optional[int], Optional[TraceRow], Optional[TraceRow], float]):
        ia, ib, ra, rb, _ = item
        phase = (ra or rb).get("phase") if (ra or rb) else ""
        index = ia if ia is not None else ib
        return (str(phase), index if index is not None else -1)

    combined.sort(key=sort_key)
    return [(ra, rb, score) for ia, ib, ra, rb, score in combined]


def diff_metrics(a_tot: Mapping[str, float], b_tot: Mapping[str, float]) -> Dict[str, Dict[str, float]]:
    """Return per-metric {'metric': {'a':x,'b':y,'delta':y-x,'pct':(y-x)/max(x,1e-9)}} for keys present."""
    metrics: Dict[str, Dict[str, float]] = {}
    keys = set(a_tot.keys()) | set(b_tot.keys())
    for k in keys:
        a_val = float(a_tot.get(k, 0.0))
        b_val = float(b_tot.get(k, 0.0))
        delta = b_val - a_val
        pct = delta / max(a_val, 1e-9)
        metrics[k] = {"a": a_val, "b": b_val, "delta": delta, "pct": pct}
    return metrics


def diff_table_rows(
    aligned: Sequence[Tuple[Optional[TraceRow], Optional[TraceRow], float]]
) -> List[Dict[str, object]]:
    """
    Produce flat rows with: phase, name, a_status, b_status, a_dur_ms, b_dur_ms, d_dur_ms,
    a_tokens, b_tokens, d_tokens, a_cost, b_cost, d_cost, match_score.
    """
    rows: List[Dict[str, object]] = []
    for ra, rb, score in aligned:
        phase = (ra or rb).get("phase")
        name = (ra or rb).get("name")
        a_dur = ra.get("duration_ms") if ra else None
        b_dur = rb.get("duration_ms") if rb else None
        a_tok = ra.get("tokens") if ra else None
        b_tok = rb.get("tokens") if rb else None
        a_cost = ra.get("cost") if ra else None
        b_cost = rb.get("cost") if rb else None
        rows.append(
            {
                "phase": phase,
                "name": name,
                "a_status": ra.get("status") if ra else None,
                "b_status": rb.get("status") if rb else None,
                "a_dur_ms": a_dur,
                "b_dur_ms": b_dur,
                "d_dur_ms": (b_dur or 0) - (a_dur or 0),
                "a_tokens": a_tok,
                "b_tokens": b_tok,
                "d_tokens": (b_tok or 0) - (a_tok or 0),
                "a_cost": a_cost,
                "b_cost": b_cost,
                "d_cost": (b_cost or 0) - (a_cost or 0),
                "match_score": score,
            }
        )
    rows.sort(key=lambda r: (str(r.get("phase")), r.get("name") or ""))
    return rows


def to_csv(rows: List[Dict[str, object]]) -> bytes:
    output = io.StringIO()
    fieldnames = list(rows[0].keys()) if rows else []
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def to_markdown(summary: Mapping[str, Mapping[str, float]], rows: List[Dict[str, object]]) -> bytes:
    lines: List[str] = []
    lines.append("# Run Comparison\n")
    lines.append("## Summary\n")
    for k, v in summary.items():
        lines.append(
            f"- {k}: {v['a']} → {v['b']} (Δ {v['delta']}, {v['pct']*100:.1f}% )"
        )
    lines.append("")
    lines.append("## Changed steps\n")
    headers = [
        "phase",
        "name",
        "a_status",
        "b_status",
        "a_dur_ms",
        "b_dur_ms",
        "d_dur_ms",
        "a_tokens",
        "b_tokens",
        "d_tokens",
        "a_cost",
        "b_cost",
        "d_cost",
        "match_score",
    ]
    lines.append("|" + "|".join(headers) + "|")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        lines.append("|" + "|".join(str(r.get(h, "")) for h in headers) + "|")
    lines.append("")
    return "\n".join(lines).encode("utf-8")


__all__ = [
    "aggregate_from_rows",
    "align_steps",
    "diff_metrics",
    "diff_table_rows",
    "to_csv",
    "to_markdown",
]
