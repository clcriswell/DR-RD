from __future__ import annotations

import json
from typing import Any, Tuple

from .json_safety import strip_fences, auto_repair_json, light_sanitize, parse_json_loose
from .agent_json import extract_json_block


def attempt_auto_fix(raw: str) -> Tuple[bool, Any]:
    """Attempt to repair malformed JSON strings.

    Parameters
    ----------
    raw:
        The raw string emitted by an LLM.

    Returns
    -------
    tuple[bool, Any]
        ``(True, obj)`` if JSON could be parsed into ``obj``; ``(False, cleaned)``
        where ``cleaned`` is a sanitized string otherwise.
    """

    if not isinstance(raw, str):
        return False, raw

    cleaned = strip_fences(raw)
    cleaned = light_sanitize(cleaned)
    cleaned = auto_repair_json(cleaned)

    try:
        return True, json.loads(cleaned)
    except Exception:
        pass

    obj = extract_json_block(cleaned)
    if obj is not None:
        return True, obj

    try:
        return True, parse_json_loose(cleaned)
    except Exception:
        return False, cleaned
