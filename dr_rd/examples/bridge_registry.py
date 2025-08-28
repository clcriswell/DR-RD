from __future__ import annotations

from typing import List, Dict

from . import catalog


def get_examples(role: str, n: int = 3) -> List[Dict]:
    """Fetch ``n`` exemplar snippets for ``role``."""
    return catalog.fetch(role, n)
