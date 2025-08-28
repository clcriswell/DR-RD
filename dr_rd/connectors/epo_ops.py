from __future__ import annotations

import os
from typing import Any, Dict

from .commons import cached


@cached(ttl_s=86400)
def search_patents(query: str) -> Dict[str, Any]:
    if not os.getenv("EPO_OPS_KEY"):
        raise RuntimeError("EPO_OPS_KEY not set")
    return {"items": []}


@cached(ttl_s=86400)
def fetch_patent(pub_number: str) -> Dict[str, Any]:
    if not os.getenv("EPO_OPS_KEY"):
        raise RuntimeError("EPO_OPS_KEY not set")
    return {"record": {}}


__all__ = ["search_patents", "fetch_patent"]
