import re
import secrets
from pathlib import Path

from . import knowledge_store

SAFE_EXTS = {".txt", ".md", ".pdf", ".docx", ".csv", ".json"}


def sanitize_filename(name: str) -> str:
    """Return a safe filename by stripping risky characters and collapsing spaces."""
    name = re.sub(r"[^A-Za-z0-9._-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"\s+\.", ".", name)
    return name or "file"


def unique_upload_path(original_name: str) -> Path:
    """Return a unique path under ``knowledge_store.UPLOADS`` for ``original_name``."""
    safe = sanitize_filename(original_name)
    stem = Path(safe).stem
    suffix = Path(safe).suffix
    token = secrets.token_hex(4)
    filename = f"{stem}_{token}{suffix}"
    return knowledge_store.UPLOADS / filename


def allowed_ext(name: str) -> bool:
    """Return True if ``name`` has an allowed extension."""
    return Path(name).suffix.lower() in SAFE_EXTS
