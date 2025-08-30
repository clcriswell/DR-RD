from utils import compare


def test_diff_configs_and_metrics():
    a = {"model": "gpt-4", "nested": {"a": 1, "ts": 1}}
    b = {"model": "gpt-4", "nested": {"a": 2, "ts": 2}}
    diffs = compare.diff_configs(a, b)
    assert ("nested.a", 1, 2) in diffs
    assert all(path != "nested.ts" for path, _, _ in diffs)

    mets = compare.diff_metrics({"tokens": 10}, {"tokens": 20})
    assert mets["tokens"]["delta"] == 10
    assert mets["tokens"]["pct"] == 1.0
    mets = compare.diff_metrics({"tokens": 0}, {"tokens": 5})
    assert mets["tokens"]["pct"] == float("inf")


def test_align_steps_and_markdown():
    rows_a = [
        {"id": "1", "phase": "p", "name": "A", "summary": "foo", "status": "ok"},
        {"id": "2", "phase": "p", "name": "B", "summary": "bar", "status": "ok"},
        {"id": "3", "phase": "p", "name": "C", "summary": "baz", "status": "ok"},
    ]
    rows_b = [
        {"id": "x", "phase": "p", "name": "A", "summary": "foo", "status": "ok"},
        {"id": "y", "phase": "p", "name": "C", "summary": "baz", "status": "ok"},
        {"id": "z", "phase": "p", "name": "D", "summary": "qux", "status": "ok"},
    ]
    aligned = compare.align_steps(rows_a, rows_b)
    assert any(s.a_id == "2" and s.b_id is None for s in aligned)
    assert any(s.a_id is None and s.b_id == "z" for s in aligned)

    run_a = {
        "run_id": "ra",
        "meta": {"started_at": 0, "completed_at": 1},
        "lock": {},
        "trace_rows": rows_a,
        "totals": {"tokens": 3, "cost_usd": 0.0, "duration_s": 0.0},
    }
    run_b = {
        "run_id": "rb",
        "meta": {"started_at": 0, "completed_at": 1},
        "lock": {},
        "trace_rows": rows_b,
        "totals": {"tokens": 3, "cost_usd": 0.0, "duration_s": 0.0},
    }
    md = compare.to_markdown(run_a, run_b, [], compare.diff_metrics(run_a["totals"], run_b["totals"]), aligned)
    assert "ra" in md and "rb" in md
    assert "|metric|" in md

