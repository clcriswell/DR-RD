from __future__ import annotations

import hashlib
import json
import secrets
import time
from pathlib import Path
from typing import Iterable, Mapping, Optional

from .lazy_import import local_import

ROOT = Path(".dr_rd/knowledge")
UPLOADS = ROOT / "uploads"
META = ROOT / "meta.json"


def init_store() -> None:
    """Ensure the knowledge store directories and metadata file exist."""
    ROOT.mkdir(parents=True, exist_ok=True)
    UPLOADS.mkdir(parents=True, exist_ok=True)
    if not META.exists():
        _write_meta({})


def _read_meta() -> dict[str, dict]:
    if META.exists():
        try:
            return json.loads(META.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _write_meta(data: Mapping[str, dict]) -> None:
    META.parent.mkdir(parents=True, exist_ok=True)
    tmp = META.parent / (META.name + ".tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(META)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def list_items(tags: Iterable[str] | None = None) -> list[dict]:
    """Return a sorted list of item dicts."""
    meta = _read_meta()
    items = list(meta.values())
    if tags:
        tagset = set(tags)
        items = [i for i in items if tagset.intersection(i.get("tags", []))]
    items.sort(key=lambda x: x.get("created_at", 0))
    return items


def get_item(item_id: str) -> dict | None:
    return _read_meta().get(item_id)


def _ensure_inside_uploads(path: Path) -> None:
    try:
        path.resolve().relative_to(UPLOADS.resolve())
    except Exception as exc:
        raise ValueError("path outside uploads") from exc


def add_item(
    name: str, path: Path, *, tags: list[str] | None, kind: str, pii_flag: bool = False
) -> dict:
    """Register an item already copied into uploads and return its metadata."""
    init_store()
    _ensure_inside_uploads(path)
    meta = _read_meta()
    item_id = f"kn_{int(time.time())}_{secrets.token_hex(4)}"
    size = path.stat().st_size
    type_ = path.suffix.lstrip(".").upper()
    with path.open("rb") as fh:
        sha256 = hashlib.sha256(fh.read()).hexdigest()
    item = {
        "id": item_id,
        "name": name,
        "tags": tags or [],
        "type": type_,
        "size": size,
        "created_at": time.time(),
        "path": str(path),
        "kind": kind,
        "sha256": sha256,
        "pii_flag": bool(pii_flag),
    }
    meta[item_id] = item
    _write_meta(meta)
    return item


def remove_item(item_id: str) -> bool:
    meta = _read_meta()
    item = meta.pop(item_id, None)
    if not item:
        return False
    try:
        Path(item["path"]).unlink(missing_ok=True)
    except OSError:
        pass
    _write_meta(meta)
    return True


def set_tags(item_id: str, tags: list[str]) -> dict:
    meta = _read_meta()
    item = meta.get(item_id)
    if not item:
        raise KeyError(item_id)
    item["tags"] = tags
    meta[item_id] = item
    _write_meta(meta)
    return item


def load_text(item_id: str, *, max_chars: int | None = None) -> Optional[str]:
    """Best effort load of item text for indexing.

    Supports .txt, .md, .json, .csv, .pdf, .docx. Returns None on failure.
    """
    item = get_item(item_id)
    if not item:
        return None
    path = Path(item.get("path", ""))
    ext = path.suffix.lower()
    try:
        if ext in {".txt", ".md", ".json", ".csv"}:
            text = path.read_text("utf-8", errors="ignore")
        elif ext == ".pdf":
            try:
                pdf = local_import("pdfminer.high_level")
                text = pdf.extract_text(str(path))
            except Exception:
                return None
        elif ext == ".docx":
            try:
                docx = local_import("docx")
                doc = docx.Document(str(path))
                text = "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                return None
        else:
            return None
        if max_chars is not None:
            return text[:max_chars]
        return text
    except Exception:
        return None


def as_choice_list() -> list[tuple[str, str]]:
    """Return a list of ``(label, id)`` tuples for UI multiselects."""
    choices: list[tuple[str, str]] = []
    for item in list_items():
        size_kb = item["size"] / 1024
        size_str = f"{int(size_kb)} KB"
        label = f"{item['name']} ({item['type']}, {size_str})"
        choices.append((label, item["id"]))
    return choices
