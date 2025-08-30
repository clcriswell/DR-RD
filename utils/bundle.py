from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from typing import Callable, Iterable, Tuple

DEFAULT_FILES = [
    ("trace", "json"),
    ("summary", "csv"),
    ("report", "md"),
]


def build_zip_bundle(
    run_id: str,
    files: Iterable[Tuple[str, str]],
    *,
    read_bytes: Callable[[str, str, str], bytes],
    list_existing: Callable[[str], Iterable[Tuple[str, str]]],
) -> bytes:
    """Create an in-memory ZIP for the run."""
    to_include = set(DEFAULT_FILES)
    to_include.update(files)
    for name_ext in list_existing(run_id):
        to_include.add(name_ext)

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as zf:
        for name, ext in sorted(to_include):
            try:
                data = read_bytes(run_id, name, ext)
            except Exception:
                continue
            zf.writestr(f"{name}.{ext}", data)
    return buffer.getvalue()


__all__ = ["build_zip_bundle", "DEFAULT_FILES"]
