from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def route_failure(
    metrics: Dict[str, Any], outputs_dir: Path, context: Dict[str, Any] | None = None
) -> None:
    """Persist a minimal triage payload for QA follow-up."""
    outputs_dir = Path(outputs_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    payload = {"metrics": metrics, "context": context or {}}
    with open(outputs_dir / "qa_queue.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    # TODO: integrate with issue tracker
