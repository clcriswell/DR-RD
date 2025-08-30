from typing import Mapping, Sequence, Tuple
from pathlib import Path
import json

from .paths import write_bytes, write_text, ensure_run_dirs
from .trace_export import flatten_trace_rows
from .metrics import ensure_run_totals
from .telemetry import log_event
from .runs import create_run_meta, complete_run_meta

DEMO_DIR = Path("samples/demo_run")


def load_demo_meta() -> dict:
    """Load and merge demo run metadata."""
    cfg_text = (DEMO_DIR / "run_config.lock.json").read_text(encoding="utf-8")
    env_text = (DEMO_DIR / "env.snapshot.json").read_text(encoding="utf-8")
    cfg = json.loads(cfg_text)
    env = json.loads(env_text)
    meta = {**cfg, "env": env}
    return meta


def load_demo_trace() -> list[dict]:
    """Return the recorded trace."""
    return json.loads((DEMO_DIR / "trace.json").read_text(encoding="utf-8"))


def load_demo_summary() -> Tuple[str, bytes]:
    """Return report text and summary CSV bytes."""
    report = (DEMO_DIR / "report.md").read_text(encoding="utf-8")
    csv_bytes = (DEMO_DIR / "summary.csv").read_bytes()
    return report, csv_bytes


def materialize_run(run_id: str) -> dict:
    """Copy demo artifacts into a real run folder and return data for UI."""
    ensure_run_dirs(run_id)
    cfg_text = (DEMO_DIR / "run_config.lock.json").read_text(encoding="utf-8")
    env_text = (DEMO_DIR / "env.snapshot.json").read_text(encoding="utf-8")
    meta = load_demo_meta()
    trace = load_demo_trace()
    report_md, summary_csv = load_demo_summary()

    create_run_meta(run_id, mode="demo", idea_preview=meta.get("idea", "")[:120])
    write_bytes(run_id, "trace", "json", json.dumps(trace, ensure_ascii=False, indent=2).encode("utf-8"))
    write_bytes(run_id, "summary", "csv", summary_csv)
    write_text(run_id, "report", "md", report_md)
    write_text(run_id, "run_config", "lock.json", cfg_text)
    write_text(run_id, "env", "snapshot.json", env_text)

    rows = flatten_trace_rows(trace)
    totals = ensure_run_totals(None, rows)
    complete_run_meta(run_id, status="success")
    log_event({"event": "run_created", "run_id": run_id, "mode": "demo"})
    log_event({"event": "run_completed", "run_id": run_id, "status": "success"})
    return {"meta": meta, "trace": trace, "totals": totals, "report_md": report_md}


__all__ = [
    "load_demo_meta",
    "load_demo_trace",
    "load_demo_summary",
    "materialize_run",
]
