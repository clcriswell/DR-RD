from __future__ import annotations

"""Utilities for loading and normalizing evaluation datasets."""

from typing import Iterable, Dict, Any, List
import csv
import json
from pathlib import Path

ALLOWED_KEYS = {
    "id",
    "idea",
    "mode",
    "limits",
    "expected_keywords",
    "forbidden_keywords",
    "min_words",
    "max_words",
    "tags",
    "seed",
    "rubric",
}


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def load_csv(path: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append({k: v for k, v in row.items() if v != ""})
    return items


def _split_list(val: Any) -> List[str]:
    if isinstance(val, list):
        return [str(v).strip() for v in val if str(v).strip()]
    if isinstance(val, str):
        return [v.strip() for v in val.split(",") if v.strip()]
    return []


def normalize(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    norm: List[Dict[str, Any]] = []
    for raw in items:
        item = {k: raw[k] for k in raw.keys() & ALLOWED_KEYS}
        if unknown := set(raw) - ALLOWED_KEYS:
            # drop unknown keys silently
            pass
        _id = str(item.get("id") or "").strip()
        if not _id:
            raise ValueError("missing id")
        if _id in seen:
            raise ValueError(f"duplicate id: {_id}")
        seen.add(_id)
        item["id"] = _id
        item["idea"] = str(item.get("idea") or "").strip()
        item["mode"] = str(item.get("mode") or "standard")
        limits = item.get("limits") or {}
        if not isinstance(limits, dict):
            limits = {}
        budget = limits.get("budget_usd") or raw.get("budget_usd")
        max_toks = limits.get("max_tokens") or raw.get("max_tokens")
        item["limits"] = {
            "budget_usd": float(budget) if budget is not None else None,
            "max_tokens": int(max_toks) if max_toks is not None else None,
        }
        item["expected_keywords"] = _split_list(raw.get("expected_keywords"))
        item["forbidden_keywords"] = _split_list(raw.get("forbidden_keywords"))
        item["tags"] = _split_list(raw.get("tags"))
        for k in ("min_words", "max_words", "seed"):
            if k in raw and raw[k] is not None and raw[k] != "":
                item[k] = int(raw[k])
        if "rubric" in raw:
            item["rubric"] = str(raw["rubric"])
        norm.append(item)
    return norm


def save_jsonl(path: str, items: Iterable[Dict[str, Any]]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
