from __future__ import annotations

"""Thin helpers bridging the Streamlit UI to core execution paths."""

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.agents import unified_registry
from core import runner
from dr_rd.agents.dynamic_agent import DynamicAgent
from core.llm import select_model
from core.trace_diff import load_run as _load_run, diff_runs as _diff_runs
from dr_rd.incidents.bundle import make_incident_bundle as _make_bundle
from dr_rd.safety.redaction_review import summarize_redactions


@contextmanager
def _apply_flag_overrides(overrides: Optional[Dict[str, Any]]):
    """Temporarily apply feature-flag overrides for the duration of a call."""
    if not overrides:
        yield
        return
    from config import feature_flags as ff

    original: Dict[str, Any] = {}
    for key, val in overrides.items():
        if hasattr(ff, key):
            original[key] = getattr(ff, key)
            setattr(ff, key, val)
    try:
        yield
    finally:
        for key, val in original.items():
            setattr(ff, key, val)


# ---------------------------------------------------------------------------
# Specialists
# ---------------------------------------------------------------------------


def run_specialist(
    role: str,
    title: str,
    desc: str,
    inputs: Dict[str, Any],
    flag_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute a registered specialist role and return its JSON output."""

    # Resolve to ensure the role exists; reuse existing instance if possible.
    agent = unified_registry.get_agent(role)
    with _apply_flag_overrides(flag_overrides):
        return runner.execute_task(role, title, desc, inputs, flag_overrides, agent)


# ---------------------------------------------------------------------------
# Dynamic agent
# ---------------------------------------------------------------------------


def run_dynamic(
    spec: Dict[str, Any],
    flag_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Instantiate and run a DynamicAgent with the provided spec."""

    model = select_model("agent", agent_name="Dynamic Specialist")
    agent = DynamicAgent(model)
    with _apply_flag_overrides(flag_overrides):
        data, _schema = agent.run(spec)
    return data


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def load_provenance(
    log_dir: Optional[str] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    """Load provenance events newest-first from ``log_dir``."""

    base = Path(log_dir or os.getenv("PROVENANCE_LOG_DIR", "runs"))  # type: ignore
    entries: List[Dict[str, Any]] = []
    for fp in sorted(base.glob("*/provenance.jsonl")):
        try:
            for line in fp.read_text().splitlines():
                if not line.strip():
                    continue
                entries.append(json.loads(line))
        except Exception:
            continue
    entries.sort(key=lambda e: e.get("ts", 0), reverse=True)
    return entries[:limit]


# ---------------------------------------------------------------------------
# Trace operations
# ---------------------------------------------------------------------------


def list_runs(log_root: str | Path = "runs") -> List[Dict[str, Any]]:
    """Return available runs under ``log_root``."""
    root = Path(log_root)
    runs: List[Dict[str, Any]] = []
    for rd in sorted(root.glob("*/run_meta.json")):
        data = json.loads(rd.read_text())
        runs.append({"id": data.get("run_id"), "started_at": data.get("started_at"), "path": str(rd.parent)})
    return runs


def load_run(path: str | Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    meta, spans = _load_run(path)
    return json.loads(json.dumps(meta.__dict__)), [s.__dict__ for s in spans]


def diff_runs(base_path: str | Path, cand_path: str | Path) -> Dict[str, Any]:
    return _diff_runs(_load_run(base_path), _load_run(cand_path))


def make_incident_bundle(base_path: str | Path, cand_path: str | Path, out_dir: str | Path) -> str:
    return _make_bundle(base_path, cand_path, out_dir)


def redaction_summary(path: str | Path) -> Dict[str, Any]:
    _, spans = _load_run(path)
    return summarize_redactions(spans)


__all__ = [
    "run_specialist",
    "run_dynamic",
    "load_provenance",
    "list_runs",
    "load_run",
    "diff_runs",
    "make_incident_bundle",
    "redaction_summary",
]
