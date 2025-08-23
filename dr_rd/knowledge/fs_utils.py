from __future__ import annotations

from pathlib import Path

# Required files for a FAISS bundle; adjust if retriever expectations change.
REQUIRED_FILES = ["index.faiss", "texts.json"]


def bundle_complete(path: str | Path) -> bool:
    """Return True if the given directory contains a usable FAISS bundle."""
    p = Path(path)
    return all((p / name).exists() for name in REQUIRED_FILES)
