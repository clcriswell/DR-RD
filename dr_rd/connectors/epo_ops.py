from __future__ import annotations

from typing import Any, Dict

from dr_rd.config.env import require_env
from .commons import cached


@cached(ttl_s=86400)
def search_patents(query: str) -> Dict[str, Any]:
    require_env("EPO_OPS_KEY")
    return {"items": []}


@cached(ttl_s=86400)
def fetch_patent(pub_number: str) -> Dict[str, Any]:
    require_env("EPO_OPS_KEY")
    return {"record": {}}


__all__ = ["search_patents", "fetch_patent"]
