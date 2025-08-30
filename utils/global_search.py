from __future__ import annotations

from typing import List, Dict, Any, Tuple, Optional
import difflib
import time

# Optional fast fuzzy matcher
try:  # pragma: no cover - optional dependency
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover - fallback
    fuzz = None  # type: ignore

from . import runs_index, run_notes, knowledge_store


# Result schema:
# {'kind': 'page'|'cmd'|'run'|'knowledge',
#  'id': 'trace'|'reports'|run_id|item_id|...,
#  'label': 'Trace — 2025-08-29 — Idea…',
#  'hint': 'Open page'|'Open trace'|'Open reports'|'Use source'|...,
#  'score': float,
#  'payload': {...}}  # for actions


def build_corpus(*, runs: List[Dict], notes: Dict[str, Dict], knowledge: List[Dict]) -> List[Dict]:
    """Return a flat list of candidate objects with searchable text fields assembled."""
    corpus: List[Dict] = []
    for r in runs:
        rid = r.get("run_id", "")
        note = notes.get(rid, {})
        title = note.get("title") or r.get("idea_preview", "")
        ts = r.get("started_at") or 0
        date = time.strftime("%Y-%m-%d", time.localtime(ts)) if ts else ""
        hay = " ".join(
            [
                rid,
                r.get("idea_preview", ""),
                title,
                note.get("note", ""),
                " ".join(note.get("tags", [])),
            ]
        )
        label = f"Trace — {date} — {title}"
        corpus.append(
            {
                "kind": "run",
                "id": f"{rid}:trace",
                "label": label,
                "hint": "Open trace",
                "payload": {"view": "trace", "run_id": rid},
                "text": hay,
            }
        )
        label_r = f"Reports — {date} — {title}"
        corpus.append(
            {
                "kind": "run",
                "id": f"{rid}:reports",
                "label": label_r,
                "hint": "Open reports",
                "payload": {"view": "reports", "run_id": rid},
                "text": hay,
            }
        )
    for item in knowledge:
        text = " ".join([item.get("name", ""), " ".join(item.get("tags", []))])
        corpus.append(
            {
                "kind": "knowledge",
                "id": item.get("id"),
                "label": item.get("name", ""),
                "hint": "Use source",
                "payload": {"item_id": item.get("id")},
                "text": text,
            }
        )
    return corpus


def _score(query: str, text: str) -> float:
    q = query.lower()
    hay = text.lower()
    if not q:
        return 1.0
    if q in hay:
        return 1.0
    if fuzz:
        return fuzz.ratio(q, hay) / 100.0  # type: ignore[return-value]
    return difflib.SequenceMatcher(None, q, hay).ratio()


def fuzzy_rank(query: str, candidates: List[Dict], limit: int = 20) -> List[Dict]:
    """Use difflib.SequenceMatcher or rapidfuzz if available; return top-N with 'score'."""
    scored: List[Tuple[float, Dict]] = []
    for c in candidates:
        text = " ".join([c.get("label", ""), c.get("text", "")])
        score = _score(query, text)
        scored.append((score, c))
    scored.sort(key=lambda t: t[0], reverse=True)
    out: List[Dict] = []
    for score, c in scored[:limit]:
        item = {k: v for k, v in c.items() if k != "text"}
        item["score"] = score
        out.append(item)
    return out


def default_actions() -> List[Dict]:
    """Static command/page entries with labels and payloads."""
    actions: List[Dict] = []
    pages = [
        ("run", "Run", "app.py"),
        ("trace", "Trace", "pages/10_Trace.py"),
        ("reports", "Reports", "pages/20_Reports.py"),
        ("metrics", "Metrics", "pages/30_Metrics.py"),
        ("compare", "Compare", "pages/25_Compare.py"),
        ("knowledge", "Knowledge", "pages/15_Knowledge.py"),
        ("history", "History", "pages/12_History.py"),
        ("settings", "Settings", "pages/90_Settings.py"),
        ("health", "Health", "pages/05_Health.py"),
    ]
    for pid, label, page in pages:
        actions.append(
            {
                "kind": "page",
                "id": pid,
                "label": label,
                "hint": "Open page",
                "payload": {"page": page},
                "text": label,
            }
        )
    runs = runs_index.load_index()
    last_run = runs[0] if runs else None
    last_run_id = last_run.get("run_id") if last_run else None
    resumable = next((r for r in runs if r.get("status") == "resumable"), None)
    resumable_id = resumable.get("run_id") if resumable else None
    actions.append(
        {
            "kind": "cmd",
            "id": "start_demo",
            "label": "Start demo run",
            "hint": "Start demo",
            "payload": {},
            "text": "start demo run",
        }
    )
    if last_run_id:
        actions.append(
            {
                "kind": "cmd",
                "id": "repro_last_run",
                "label": "Reproduce last run",
                "hint": "Prefill from last run",
                "payload": {"run_id": last_run_id},
                "text": f"reproduce {last_run_id}",
            }
        )
        actions.append(
            {
                "kind": "cmd",
                "id": "open_latest_trace",
                "label": "Open latest trace",
                "hint": "Go to last trace",
                "payload": {"run_id": last_run_id},
                "text": f"latest trace {last_run_id}",
            }
        )
    if resumable_id:
        actions.append(
            {
                "kind": "cmd",
                "id": "resume_last_run",
                "label": "Resume last run",
                "hint": "Resume last resumable run",
                "payload": {"run_id": resumable_id},
                "text": f"resume {resumable_id}",
            }
        )
    actions.append(
        {
            "kind": "cmd",
            "id": "copy_share_link",
            "label": "Copy share link",
            "hint": "Copy share link",
            "payload": {"text": ""},
            "text": "copy share link",
        }
    )
    from pathlib import Path

    if Path(".dr_rd/flags.json").exists():  # feature flags file present
        actions.append(
            {
                "kind": "cmd",
                "id": "open_flags",
                "label": "Open flags",
                "hint": "Open flags",
                "payload": {},
                "text": "open flags",
            }
        )
    return actions


def search(query: str, *, limit: int = 20) -> List[Dict]:
    """Load runs/notes/knowledge; build corpus + default actions; return ranked results."""
    runs = runs_index.load_index()
    notes = run_notes.all_notes()
    knowledge = knowledge_store.list_items()
    candidates = build_corpus(runs=runs, notes=notes, knowledge=knowledge)
    candidates.extend(default_actions())
    return fuzzy_rank(query, candidates, limit=limit)


def resolve_action(item: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a selected item into a normalized action."""
    kind = item.get("kind")
    payload = item.get("payload", {})
    if kind == "page":
        return {"action": "switch_page", "params": payload, "kind": kind}
    if kind == "run":
        return {"action": "set_params", "params": payload, "kind": kind}
    if kind == "knowledge":
        return {"action": "set_params", "params": {"use_source": payload.get("item_id"), "view": "run"}, "kind": kind}
    if kind == "cmd":
        cid = item.get("id")
        if cid == "start_demo":
            return {"action": "start_demo", "params": {}, "kind": kind}
        if cid == "repro_last_run":
            rid = payload.get("run_id")
            return {"action": "set_params", "params": {"origin_run_id": rid, "view": "run"}, "kind": kind}
        if cid == "resume_last_run":
            rid = payload.get("run_id")
            return {"action": "set_params", "params": {"resume_from": rid, "view": "run"}, "kind": kind}
        if cid == "copy_share_link":
            return {"action": "copy", "params": {"text": payload.get("text", "")}, "kind": kind}
        if cid == "open_latest_trace":
            rid = payload.get("run_id")
            return {"action": "set_params", "params": {"view": "trace", "run_id": rid}, "kind": kind}
        if cid == "open_flags":
            return {"action": "set_params", "params": {"flags": "1"}, "kind": kind}
    return {"action": "noop", "params": {}, "kind": kind}


__all__ = [
    "build_corpus",
    "fuzzy_rank",
    "default_actions",
    "search",
    "resolve_action",
]
