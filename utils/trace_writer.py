import json
from pathlib import Path
from typing import Mapping, Any


def trace_path(run_id: str) -> Path:
    from .paths import run_root

    return run_root(run_id) / "trace.json"


def _read_trace(p: Path) -> list[Any]:
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def read_trace(run_id: str) -> list[Any]:
    """Return the saved trace list for ``run_id`` or an empty list."""

    p = trace_path(run_id)
    return _read_trace(p) if p.exists() else []


def _atomic_write(p: Path, data: list[Any]) -> None:
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def append_step(run_id: str, step: Mapping[str, Any]) -> None:
    """
    Read existing trace list (or []), append step dict, write back atomically.
    Keep file small: do not write token chunks; only final step summary/meta.
    """

    p = trace_path(run_id)
    data = _read_trace(p) if p.exists() else []
    data.append(dict(step))
    _atomic_write(p, data)


def flush_phase_meta(run_id: str, phase: str, meta: Mapping[str, Any]) -> None:
    """Optional: write/update a small 'phase_meta.json' for quick UI reads."""

    from .paths import run_root

    root = run_root(run_id)
    p = root / "phase_meta.json"
    try:
        existing = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        existing = {}
    existing[phase] = dict(meta)
    _atomic_write(p, existing)


__all__ = ["trace_path", "append_step", "flush_phase_meta", "read_trace"]
