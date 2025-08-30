from __future__ import annotations

import re
import time
import uuid

_RUN_ID_RE = re.compile(r"^\d{10}-[0-9a-f]{8}$")


def new_run_id() -> str:
    """Return a sortable run identifier.

    Format: ``{epoch_seconds}-{uuid8}``
    """
    return f"{int(time.time())}-{uuid.uuid4().hex[:8]}"


def is_run_id(s: str) -> bool:
    """Return True if ``s`` looks like a run_id."""
    return bool(_RUN_ID_RE.fullmatch(s))
