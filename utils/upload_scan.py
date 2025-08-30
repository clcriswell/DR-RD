import mimetypes
import os
import re
from pathlib import Path

SAFE_TYPES = {
    "text/plain",
    "text/markdown",
    "application/pdf",
    "application/json",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

MAX_BYTES = int(os.getenv("UPLOAD_MAX_BYTES", 20_000_000))


def sniff_type(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def allowed(path: Path) -> bool:
    typ = sniff_type(path)
    return typ in SAFE_TYPES and path.stat().st_size <= MAX_BYTES


def detect_pii(text: str) -> bool:
    from .redaction import PII_PATTERNS

    return any(re.search(p, text) for p in PII_PATTERNS)
