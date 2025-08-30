from pathlib import Path
import json, time, os, tempfile, shutil
from typing import Any, Dict, Optional

from utils.telemetry import checkpoint_saved

ROOT = Path(".dr_rd/runs")


def path(run_id: str) -> Path:
    p = ROOT / run_id / "checkpoint.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load(run_id: str) -> Optional[Dict[str, Any]]:
    cp = path(run_id)
    if not cp.exists():
        return None
    with cp.open("r", encoding="utf-8") as f:
        return json.load(f)


def _atomic_write(p: Path, obj: Dict[str, Any]) -> None:
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)


def init(run_id: str, *, phases: list[str]) -> Dict[str, Any]:
    cp = {
        "run_id": run_id,
        "created_at": time.time(),
        "phases": {ph: {"completed": [], "next_index": 0} for ph in phases},
    }
    _atomic_write(path(run_id), cp)
    return cp


def mark_step_done(
    run_id: str,
    phase: str,
    step_id: str | int,
    outputs_meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    cp = load(run_id) or {"phases": {}}
    phase_cp = cp["phases"].setdefault(phase, {"completed": [], "next_index": 0})
    phase_cp["completed"].append({"step_id": step_id, "at": time.time(), "meta": outputs_meta or {}})
    phase_cp["next_index"] = len(phase_cp["completed"])
    _atomic_write(path(run_id), cp)
    checkpoint_saved(run_id, phase, step_id)
    return cp


def last_completed_index(run_id: str, phase: str) -> int:
    cp = load(run_id)
    if not cp:
        return 0
    ph = cp["phases"].get(phase, {})
    return int(ph.get("next_index", 0))
