import json

from utils.trace_export import flatten_trace_rows
from utils.diff_runs import (
    aggregate_from_rows,
    align_steps,
    diff_metrics,
    diff_table_rows,
)

TRACE_A = [
    {"phase": "plan", "name": "step1", "status": "complete", "duration_ms": 10, "tokens": 1, "cost": 0.1},
    {"phase": "exec", "name": "step2", "status": "complete", "duration_ms": 20, "tokens": 2, "cost": 0.2},
]

TRACE_B = [
    {"phase": "plan", "name": "step1_renamed", "status": "complete", "duration_ms": 10, "tokens": 1, "cost": 0.1},
    {"phase": "exec", "name": "step2", "status": "complete", "duration_ms": 25, "tokens": 2, "cost": 0.2},
    {"phase": "exec", "name": "step3", "status": "complete", "duration_ms": 5, "tokens": 1, "cost": 0.05},
]


def _rows(trace):
    return flatten_trace_rows(trace)


def test_align_steps_handles_changes():
    rows_a = _rows(TRACE_A)
    rows_b = _rows(TRACE_B)
    aligned = align_steps(rows_a, rows_b)
    assert any(ra and rb and ra["name"] == "step1" and rb["name"] == "step1_renamed" for ra, rb, _ in aligned)
    assert any(ra and rb and ra["name"] == "step2" and rb["name"] == "step2" for ra, rb, _ in aligned)
    assert any(ra is None and rb and rb["name"] == "step3" for ra, rb, _ in aligned)


def test_diff_metrics_math():
    a_tot = aggregate_from_rows(_rows(TRACE_A))
    b_tot = aggregate_from_rows(_rows(TRACE_B))
    diff = diff_metrics(a_tot, b_tot)
    assert diff["duration_ms"]["delta"] == b_tot["duration_ms"] - a_tot["duration_ms"]
    assert diff["steps"]["b"] == 3


def test_diff_table_rows_contains_deltas():
    aligned = align_steps(_rows(TRACE_A), _rows(TRACE_B))
    rows = diff_table_rows(aligned)
    target = [r for r in rows if r["name"] == "step2"][0]
    assert target["d_dur_ms"] == 5
    assert target["match_score"] == 1.0
