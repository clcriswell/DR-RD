import json

from utils.trace_export import to_json, to_csv, to_markdown


TRACE = [
    {
        "phase": "planner",
        "name": "Plan",
        "status": "complete",
        "started_at": 0,
        "ended_at": 1,
        "duration_ms": 1000,
        "tokens": 10,
        "cost": 0.1,
        "summary": "planning",
        "raw": {},
        "step_id": "s1",
    },
    {
        "phase": "executor",
        "name": "Exec",
        "status": "error",
        "started_at": 1,
        "ended_at": 2,
        "duration_ms": 1000,
        "tokens": 20,
        "cost": 0.2,
        "summary": "failed",
        "raw": {"error": "boom"},
        "step_id": "s2",
    },
    {
        "phase": "synth",
        "name": "Synth",
        "status": "complete",
        "started_at": 2,
        "ended_at": 3,
        "duration_ms": 1000,
        "tokens": 30,
        "cost": 0.3,
        "summary": "done",
        "raw": {},
        "step_id": "s3",
    },
]


def test_to_json_contains_ids():
    data = json.loads(to_json(TRACE).decode("utf-8"))
    assert {s["step_id"] for s in data} == {"s1", "s2", "s3"}


def test_to_csv_has_rows():
    csv_bytes = to_csv(TRACE, run_id="r1")
    lines = csv_bytes.decode("utf-8").strip().splitlines()
    assert lines[0].startswith("run_id,phase")
    assert len(lines) == 4  # header + 3 rows


def test_to_markdown_structure():
    md = to_markdown(TRACE, run_id="r1").decode("utf-8")
    assert "## Planner" in md
    assert "Step 1/" in md
