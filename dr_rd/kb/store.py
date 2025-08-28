from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .models import KBRecord, KBSource
from config import feature_flags as ff


CFG_DIR = Path(os.getenv("KNOWLEDGE_BASE_DIR", ".dr_rd/kb"))
CFG_DIR.mkdir(parents=True, exist_ok=True)
STORE_PATH = CFG_DIR / "kb.jsonl"
INDEX_PATH = CFG_DIR / "kb_index.jsonl"


def _read_all() -> List[KBRecord]:
    if not STORE_PATH.exists():
        return []
    out: List[KBRecord] = []
    with open(STORE_PATH, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                data = json.loads(line)
                sources = [KBSource(**s) for s in data.get("sources", [])]
                data["sources"] = sources
                out.append(KBRecord(**data))
            except Exception:
                continue
    return out


def add(record: KBRecord) -> str:
    """Persist ``record`` and return its id."""
    if not record.id:
        record.id = uuid.uuid4().hex
    with open(STORE_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record.asdict(), ensure_ascii=False) + "\n")
    return record.id


def get(rid: str) -> Optional[KBRecord]:
    for rec in _read_all():
        if rec.id == rid:
            return rec
    return None


def query(filters: Dict[str, Any], limit: int = 50) -> List[KBRecord]:
    out: List[KBRecord] = []
    for rec in _read_all():
        ok = True
        for k, v in filters.items():
            if getattr(rec, k, None) != v:
                ok = False
                break
        if ok:
            out.append(rec)
        if 0 < limit <= len(out):
            break
    return out


def compact() -> None:
    """Rewrite the JSONL store removing duplicate ids."""
    records = {rec.id: rec for rec in _read_all()}
    with open(STORE_PATH, "w", encoding="utf-8") as fh:
        for rec in records.values():
            fh.write(json.dumps(rec.asdict(), ensure_ascii=False) + "\n")


def kb_maybe_persist(agent_output: Dict[str, Any], route_meta: Dict[str, Any], provenance_spans: Iterable[Dict[str, Any]]) -> None:
    """Convert an agent output into a :class:`KBRecord` if KB is enabled."""
    if not getattr(ff, "KB_ENABLED", True):
        return
    try:
        sources = [KBSource(**s) for s in agent_output.get("sources", [])]
    except Exception:
        sources = []
    record = KBRecord(
        id=uuid.uuid4().hex,
        run_id=route_meta.get("run_id", ""),
        agent_role=route_meta.get("role", ""),
        task_title=route_meta.get("title", ""),
        task_desc=route_meta.get("description", ""),
        inputs=route_meta.get("inputs", {}),
        output_json=agent_output,
        sources=sources,
        ts=float(route_meta.get("ts") or 0.0),
        tags=route_meta.get("tags", []),
        metrics=route_meta.get("metrics", {}),
        provenance_span_ids=[s.get("id", "") for s in provenance_spans or []],
    )
    add(record)
