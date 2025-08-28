from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

EXAMPLE_DIR = Path("examples")
EXAMPLE_DIR.mkdir(exist_ok=True)
EXAMPLE_TOPK_PER_ROLE = 12


def _load(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def _save(path: Path, items: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")


def refresh(examples: List[Dict]) -> None:
    bucket: Dict[str, List[Dict]] = defaultdict(list)
    for ex in examples:
        bucket[ex["role"]].append(ex)
    for role, items in bucket.items():
        path = EXAMPLE_DIR / f"{role}.jsonl"
        existing = _load(path)
        all_items = existing + items
        all_items.sort(key=lambda x: (-x.get("quality_score", 0), -x.get("ts", 0)))
        _save(path, all_items[:EXAMPLE_TOPK_PER_ROLE])


def fetch(role: str, n: int = 3) -> List[Dict]:
    path = EXAMPLE_DIR / f"{role}.jsonl"
    items = _load(path)
    return items[:n]
