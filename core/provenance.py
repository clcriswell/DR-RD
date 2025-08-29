"""Provenance and span tracing utilities."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import feature_flags
from core.trace_models import RunMeta
from core.audit_log import _hmac

RUN_ID = time.strftime("%Y%m%d-%H%M%S")
_BASE = Path("runs") / RUN_ID
_FILE = _BASE / "provenance.jsonl"
_REDACTIONS_FILE = _BASE / "provenance_redactions.jsonl"
_RUN_META_FILE = _BASE / "run_meta.json"
_EVENTS: List[Dict[str, Any]] = []
_STACK: List[str] = []


def _ensure_dir() -> None:
    """Make sure the run directory exists and run meta is written."""
    _BASE.mkdir(parents=True, exist_ok=True)
    if not _RUN_META_FILE.exists():
        # Snapshot basic feature flags at start of run.
        flags = {
            k: getattr(feature_flags, k)
            for k in dir(feature_flags)
            if k.isupper()
        }
        meta = RunMeta(
            run_id=RUN_ID,
            started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            flags=flags,
            budgets={},
            models={},
        )
        _RUN_META_FILE.write_text(json.dumps(asdict(meta), default=str, indent=2))


def start_span(name: str, meta: Optional[Dict[str, Any]] = None) -> str:
    """Start a span and return its id."""
    if not feature_flags.PROVENANCE_ENABLED:
        return ""
    _ensure_dir()
    span_id = uuid.uuid4().hex
    evt = {
        "id": span_id,
        "name": name,
        "parent_id": _STACK[-1] if _STACK else None,
        "t_start": time.time(),
        "agent": meta.get("agent") if meta else None,
        "tool": meta.get("tool") if meta else None,
        "meta": meta or {},
    }
    _EVENTS.append(evt)
    _STACK.append(span_id)
    return span_id


def end_span(span_id: str, ok: bool = True, meta: Optional[Dict[str, Any]] = None) -> None:
    if not feature_flags.PROVENANCE_ENABLED:
        return
    now = time.time()
    for evt in reversed(_EVENTS):
        if evt["id"] == span_id:
            evt["t_end"] = now
            evt["duration_ms"] = int((now - evt["t_start"]) * 1000)
            evt["ok"] = ok
            if meta:
                evt.setdefault("meta", {}).update(meta)
            with _FILE.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(evt) + "\n")
            break
    if _STACK and _STACK[-1] == span_id:
        _STACK.pop()


def record_tool_provenance(
    agent: str,
    tool: str,
    args_digest: str,
    output_digest: str,
    tokens: Optional[int],
    elapsed_ms: int,
) -> None:
    span_id = start_span(tool, {"agent": agent, "tool": tool, "args_digest": args_digest})
    end_span(span_id, meta={"output_digest": output_digest, "tokens": tokens, "elapsed_ms": elapsed_ms})


def get_events() -> List[Dict[str, Any]]:
    return list(_EVENTS)


def reset() -> None:
    _EVENTS.clear()
    _STACK.clear()


def append_redaction_event(target_hash: str, reason: str, redaction_token: str) -> None:
    _ensure_dir()
    prev_hash = ""
    if _REDACTIONS_FILE.exists():
        with _REDACTIONS_FILE.open() as f:
            for line in f:
                pass
            if line.strip():
                prev_hash = json.loads(line)["hash"]
    record = {
        "ts": time.time(),
        "event": "REDACTION",
        "target_hash": target_hash,
        "reason": reason,
        "redaction_token": redaction_token,
        "prev_hash": prev_hash,
    }
    payload = json.dumps(record, sort_keys=True)
    record["hash"] = _hmac(prev_hash + payload)
    with _REDACTIONS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
