from __future__ import annotations

import json
import time
from typing import Any, Dict, List
from pathlib import Path


def to_tree(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes = {e["id"]: {**e, "children": []} for e in events}
    root = {"id": "root", "children": []}
    for e in nodes.values():
        pid = e.get("parent_id")
        if pid and pid in nodes:
            nodes[pid]["children"].append(e)
        else:
            root["children"].append(e)
    return root


def to_speedscope(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    profile_events: List[Dict[str, Any]] = []
    for e in events:
        start = int(e.get("t_start", 0) * 1000)
        end = int(e.get("t_end", e.get("t_start", 0)) * 1000)
        profile_events.append({"type": "O", "name": e.get("name"), "ts": start})
        profile_events.append({"type": "C", "name": e.get("name"), "ts": end})
    return {
        "$schema": "https://www.speedscope.app/file-format-schema.json",
        "shared": {"frames": []},
        "profiles": [
            {
                "type": "evented",
                "name": "trace",
                "events": profile_events,
            }
        ],
    }


def to_chrometrace(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    trace: List[Dict[str, Any]] = []
    for e in events:
        trace.append(
            {
                "name": e.get("name"),
                "ph": "X",
                "ts": int(e.get("t_start", 0) * 1000),
                "dur": int(e.get("duration_ms", 0)),
            }
        )
    return trace


def write_exports(events: List[Dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    (out_dir / f"trace_tree_{ts}.json").write_text(
        json.dumps(to_tree(events), indent=2), encoding="utf-8"
    )
    (out_dir / f"trace_speedscope_{ts}.json").write_text(
        json.dumps(to_speedscope(events), indent=2), encoding="utf-8"
    )
    (out_dir / f"trace_chrome_{ts}.json").write_text(
        json.dumps(to_chrometrace(events), indent=2), encoding="utf-8"
    )
