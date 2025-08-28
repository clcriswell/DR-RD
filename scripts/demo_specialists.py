from __future__ import annotations

import json
from typing import Any, Dict, List

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from core import ui_bridge


def run_demo() -> List[Dict[str, Any]]:
    """Run demo specialists and return their results."""

    off = {"RAG_ENABLED": False, "ENABLE_LIVE_SEARCH": False, "PROVENANCE_ENABLED": True}

    def _safe_call(role, title, desc, inputs, flags):
        try:
            return ui_bridge.run_specialist(role, title, desc, inputs, flags)
        except Exception as e:  # pragma: no cover - best effort
            return {"role": role, "error": str(e)}

    mat = _safe_call(
        "Materials",
        "Alloy query",
        "Lookup 6061 alloy composition",
        {"query": "6061 aluminum"},
        off,
    )
    qa = _safe_call(
        "QA",
        "QA demo",
        "Assess coverage",
        {
            "requirements": ["R1", "R2"],
            "tests": ["T1", "T2"],
            "defects": [{"id": "D1", "severity": "high"}],
        },
        off,
    )
    fin = _safe_call(
        "Finance Specialist",
        "Finance demo",
        "Unit economics",
        {
            "line_items": [{"revenue": 10, "cost": 4}],
            "cash_flows": [10, 20, 30],
            "params": {"mu": 0.1, "sigma": 0.05},
        },
        off,
    )

    on = {"RAG_ENABLED": True, "ENABLE_LIVE_SEARCH": True}
    _safe_call(
        "Materials",
        "Alloy query",
        "Lookup 6061 alloy composition",
        {"query": "6061 aluminum"},
        on,
    )

    try:
        from core import provenance

        print(f"Provenance log: {provenance._FILE}")
    except Exception:
        pass

    for obj in (mat, qa, fin):
        print(json.dumps(obj, indent=2))
    return [mat, qa, fin]


if __name__ == "__main__":  # pragma: no cover
    run_demo()
