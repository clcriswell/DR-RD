from __future__ import annotations
from pathlib import Path
from datetime import datetime

def new_run_dir(base: Path) -> Path:
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_dir = base / ts
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir
