from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict


def _load(path: Path) -> List[Dict[str, any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def merge_logs(base_path: Path, redaction_path: Path) -> List[Dict[str, any]]:
    base = _load(base_path)
    redactions = {r.get("target_hash"): r for r in _load(redaction_path)}
    merged: List[Dict[str, any]] = []
    for entry in base:
        h = entry.get("hash")
        if h in redactions:
            e = dict(entry)
            e["redacted"] = True
            e["redaction_reason"] = redactions[h].get("reason")
            e["redaction_token"] = redactions[h].get("redaction_token")
            merged.append(e)
        else:
            merged.append(entry)
    return merged
