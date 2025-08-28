from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from . import store


INDEX_FILE = store.INDEX_PATH


def rebuild() -> Dict[str, int]:
    """Rebuild a lightweight text index from the KB store."""
    records = store.query({}, limit=0)  # load all
    count = 0
    with open(INDEX_FILE, "w", encoding="utf-8") as fh:
        for rec in records:
            text = f"{rec.task_title}\n{rec.task_desc}\n{json.dumps(rec.output_json, ensure_ascii=False)}"
            obj = {"id": rec.id, "text": text, "sources": [s.id for s in rec.sources]}
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
            count += 1
    return {"records": count}


def stats() -> Dict[str, int]:
    if not INDEX_FILE.exists():
        return {"records": 0}
    with open(INDEX_FILE, "r", encoding="utf-8") as fh:
        count = sum(1 for _ in fh)
    return {"records": count}
