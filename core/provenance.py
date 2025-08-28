"""Lightweight provenance logging for tool calls."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from config import feature_flags

RUN_ID = time.strftime("%Y%m%d-%H%M%S")
_BASE = Path("runs") / RUN_ID
_FILE = _BASE / "provenance.jsonl"
_EVENTS: list[Dict[str, Any]] = []


def _ensure_dir() -> None:
    _BASE.mkdir(parents=True, exist_ok=True)


def record_tool_provenance(
    agent: str,
    tool: str,
    args_digest: str,
    output_digest: str,
    tokens: Optional[int],
    elapsed_ms: int,
) -> None:
    if not getattr(feature_flags, "PROVENANCE_ENABLED", True):
        return
    _ensure_dir()
    evt = {
        "ts": time.time(),
        "agent": agent,
        "tool": tool,
        "args_digest": args_digest,
        "output_digest": output_digest,
        "tokens": tokens,
        "elapsed_ms": elapsed_ms,
    }
    _EVENTS.append(evt)
    with _FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(evt) + "\n")


def start_span() -> float:
    return time.time()


def end_span(start: float) -> int:
    return int((time.time() - start) * 1000)


def get_events() -> list[Dict[str, Any]]:
    return list(_EVENTS)
