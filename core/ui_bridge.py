from __future__ import annotations

"""Thin helpers bridging the Streamlit UI to core execution paths."""

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.agents import unified_registry
from core import runner
from dr_rd.agents.dynamic_agent import DynamicAgent
from core.llm import select_model


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


__all__ = ["run_specialist", "run_dynamic", "load_provenance"]
