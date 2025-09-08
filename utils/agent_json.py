import json
import re
from typing import Any

from .json_safety import parse_json_loose


class AgentOutputFormatError(ValueError):
    """Raised when an agent returns malformed JSON that cannot be repaired."""


def extract_json_block(data: str | dict | list | None):
    """Return a JSON object or list from possibly messy *data*.

    Parameters
    ----------
    data:
        Text or already-parsed JSON. ``dict`` and ``list`` are returned as-is.

    Returns
    -------
    dict | list | None
        Parsed Python object if extraction succeeds, otherwise ``None``.
    """

    if isinstance(data, (dict, list)):
        return data
    if data is None:
        return None
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False)

    m = re.search(r"```json\s*(\{.*?\}|\[.*?\])\s*```", data, re.DOTALL | re.IGNORECASE)
    candidate = m.group(1) if m else data
    try:
        return json.loads(candidate)
    except Exception:
        try:
            return parse_json_loose(candidate)
        except Exception:
            return None


def extract_json_strict(text: str):
    """Return JSON object from text with one repair pass.

    If the text cannot be parsed even after stripping markdown fences, an
    :class:`AgentOutputFormatError` is raised.
    """

    try:
        return json.loads(text)
    except Exception:
        pass

    # Remove markdown fences if present
    m = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", text, re.DOTALL | re.IGNORECASE)
    candidate = m.group(1) if m else text
    try:
        return json.loads(candidate)
    except Exception as e:
        raise AgentOutputFormatError("Could not parse agent JSON") from e


def _slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:64] or "source"


def sanitize_sources(data: dict[str, Any], schema: dict) -> dict[str, Any]:
    if not isinstance(data, dict):
        return data
    props = schema.get("properties") or {}
    if "sources" not in props:
        return data
    sources = data.get("sources")
    if not isinstance(sources, list):
        return data
    sanitized: list[dict[str, Any]] = []
    for item in sources:
        if isinstance(item, dict):
            sid = item.get("id") or item.get("url") or ""
            title = item.get("title") or item.get("url") or ""
            url = item.get("url")
            entry: dict[str, Any] = {"id": sid, "title": title}
            if url:
                entry["url"] = url
            sanitized.append(entry)
        elif isinstance(item, str):
            m = re.search(r"\[(.*?)\]\((.*?)\)", item)
            if m:
                title = m.group(1).strip()
                url = m.group(2).strip()
                entry = {"id": _slugify(title) or url, "title": title}
                if url:
                    entry["url"] = url
                sanitized.append(entry)
            else:
                url = item.strip()
                entry = {"id": url, "title": url}
                if url:
                    entry["url"] = url
                sanitized.append(entry)
        # silently drop unsupported types
    new = dict(data)
    new["sources"] = sanitized
    return new
