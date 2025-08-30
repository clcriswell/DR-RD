from __future__ import annotations

import csv
import io
import json
from typing import Iterable, Mapping, Optional, List, Dict
from pathlib import Path

from .paths import RUNS_ROOT

_INDEX_PATH = Path(".dr_rd") / "runs_index.json"


def scan_runs(root: Path = RUNS_ROOT) -> List[Dict]:
    """Scan ``root`` for runs and return list of row dicts."""
    rows: List[Dict] = []
    if not root.exists():
        return rows
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        run_id = child.name
        run_path = child / "run.json"
        if run_path.exists():
            try:
                meta = json.loads(run_path.read_text(encoding="utf-8"))
            except Exception:
                meta = {"run_id": run_id}
        else:
            meta = {"run_id": run_id}
        totals_path = child / "usage_totals.json"
        tokens = 0
        cost = 0.0
        if totals_path.exists():
            try:
                totals = json.loads(totals_path.read_text(encoding="utf-8"))
                tokens = int(totals.get("tokens") or totals.get("total_tokens") or 0)
                cost = float(totals.get("cost_usd") or totals.get("cost") or 0.0)
            except Exception:
                pass
        row = {
            "run_id": meta.get("run_id", run_id),
            "started_at": meta.get("started_at"),
            "completed_at": meta.get("completed_at"),
            "status": meta.get("status"),
            "mode": meta.get("mode"),
            "idea_preview": meta.get("idea_preview", ""),
            "origin_run_id": meta.get("origin_run_id"),
            "tokens": meta.get("tokens", tokens),
            "cost_usd": meta.get("cost_usd", cost),
        }
        rows.append(row)
    rows.sort(key=lambda r: r.get("started_at") or 0, reverse=True)
    return rows


def build_index() -> List[Dict]:
    """Build the runs index and cache it."""
    rows = scan_runs()
    _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _INDEX_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    tmp.replace(_INDEX_PATH)
    return rows


def load_index(refresh: bool = False) -> List[Dict]:
    """Load cached runs index or rebuild if needed."""
    if refresh or not _INDEX_PATH.exists():
        return build_index()
    try:
        return json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return build_index()


def search(
    rows: List[Dict],
    *,
    q: str = "",
    status: Optional[Iterable[str]] = None,
    mode: Optional[Iterable[str]] = None,
    date_from: Optional[float] = None,
    date_to: Optional[float] = None,
    favorites_only: bool = False,
    tags: Optional[Iterable[str]] = None,
    notes_lookup: Mapping[str, Dict] | None = None,
) -> List[Dict]:
    """Filter ``rows`` based on provided criteria."""
    q = q.lower().strip()
    status_set = {s for s in status or []}
    mode_set = {m for m in mode or []}
    tag_set = {t.lower() for t in tags or []}
    notes_lookup = notes_lookup or {}

    def match(row: Dict) -> bool:
        rid = row.get("run_id", "")
        if status_set and row.get("status") not in status_set:
            return False
        if mode_set and row.get("mode") not in mode_set:
            return False
        if date_from and (row.get("started_at") or 0) < date_from:
            return False
        if date_to and (row.get("started_at") or 0) > date_to:
            return False
        note = notes_lookup.get(rid, {})
        if favorites_only and not note.get("favorite"):
            return False
        if tag_set and not tag_set.issubset({t.lower() for t in note.get("tags", [])}):
            return False
        if q:
            hay = " ".join(
                [
                    rid,
                    row.get("idea_preview", ""),
                    note.get("title", ""),
                    note.get("note", ""),
                    " ".join(note.get("tags", [])),
                ]
            ).lower()
            if q not in hay:
                return False
        return True

    return [r for r in rows if match(r)]


def to_csv(rows: List[Dict]) -> bytes:
    """Return ``rows`` encoded as RFC4180 CSV bytes."""
    buf = io.StringIO()
    fieldnames = [
        "run_id",
        "started_at",
        "completed_at",
        "status",
        "mode",
        "idea_preview",
        "origin_run_id",
        "tokens",
        "cost_usd",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k) for k in fieldnames})
    return buf.getvalue().encode("utf-8")


__all__ = [
    "scan_runs",
    "build_index",
    "load_index",
    "search",
    "to_csv",
]
