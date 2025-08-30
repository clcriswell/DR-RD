from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Dict

from .paths import artifact_path, ensure_run_dirs


def create_run_meta(run_id: str, *, mode: str, idea_preview: str) -> None:
    """Create initial run metadata."""
    ensure_run_dirs(run_id)
    meta = {
        "run_id": run_id,
        "started_at": int(time.time()),
        "mode": mode,
        "idea_preview": idea_preview,
        "status": "running",
    }
    artifact_path(run_id, "run", "json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def complete_run_meta(run_id: str, *, status: str) -> None:
    """Mark a run as completed with status."""
    path = artifact_path(run_id, "run", "json")
    if not path.exists():
        return
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        meta = {"run_id": run_id}
    meta.update({"completed_at": int(time.time()), "status": status})
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def load_run_meta(run_id: str) -> dict | None:
    """Load run metadata or return None."""
    path = artifact_path(run_id, "run", "json")
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_runs(limit: int = 200) -> list[dict]:
    """Return up to ``limit`` run metadata dicts, newest first."""
    root = Path(".dr_rd") / "runs"
    if not root.exists():
        return []
    metas: List[Dict] = []
    for child in sorted(root.iterdir(), reverse=True):
        if not child.is_dir():
            continue
        meta = load_run_meta(child.name)
        if meta:
            metas.append(meta)
        if len(metas) >= limit:
            break
    metas.sort(key=lambda m: m.get("started_at", 0), reverse=True)
    return metas


def last_run_id() -> str | None:
    runs = list_runs(limit=1)
    return runs[0]["run_id"] if runs else None
