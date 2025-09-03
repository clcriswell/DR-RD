from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List

from .paths import RUNS_ROOT

_MAX_NOTE_CHARS = 10_000
_MAX_TAGS = 10


def _note_path(run_id: str) -> Path:
    return RUNS_ROOT / run_id / "notes.json"


def load(run_id: str) -> Dict:
    """Load annotations for a run or return defaults."""
    path = _note_path(run_id)
    if not path.exists():
        return {"title": "", "note": "", "tags": [], "favorite": False, "updated_at": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("title", "")
            data.setdefault("note", "")
            data.setdefault("tags", [])
            data.setdefault("favorite", False)
            data.setdefault("updated_at", 0)
            return data
    except Exception:
        pass
    return {"title": "", "note": "", "tags": [], "favorite": False, "updated_at": 0}


def save(run_id: str, *, title: str, note: str, tags: List[str], favorite: bool) -> Dict:
    """Persist annotations for a run with clamped sizes."""
    note = note[:_MAX_NOTE_CHARS]
    tags = [t for t in tags if t][: _MAX_TAGS]
    data = {
        "title": title,
        "note": note,
        "tags": tags,
        "favorite": bool(favorite),
        "updated_at": int(time.time()),
    }
    path = _note_path(run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return data


def toggle_favorite(run_id: str) -> Dict:
    """Flip favorite flag for a run and persist."""
    data = load(run_id)
    fav = not bool(data.get("favorite"))
    return save(
        run_id,
        title=data.get("title", ""),
        note=data.get("note", ""),
        tags=list(data.get("tags", [])),
        favorite=fav,
    )


def all_notes() -> Dict[str, Dict]:
    """Return mapping of run_id -> notes."""
    out: Dict[str, Dict] = {}
    if not RUNS_ROOT.exists():
        return out
    for child in RUNS_ROOT.iterdir():
        if not child.is_dir():
            continue
        path = child / "notes.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    data.setdefault("title", "")
                    data.setdefault("note", "")
                    data.setdefault("tags", [])
                    data.setdefault("favorite", False)
                    data.setdefault("updated_at", 0)
                    out[child.name] = data
            except Exception:
                continue
    return out


__all__ = ["load", "save", "toggle_favorite", "all_notes"]
