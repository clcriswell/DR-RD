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
    """Normalize ``sources`` entries based on the provided *schema*.

    Handles both ``string`` and ``object`` array item types, converts markdown
    links, drops malformed items, and removes unknown keys from source objects.
    """

    if not isinstance(data, dict):
        return data
    props = schema.get("properties") or {}
    src_schema = props.get("sources")
    if not src_schema:
        return data
    sources = data.get("sources")
    if not isinstance(sources, list):
        return data

    item_schema = src_schema.get("items", {}) if isinstance(src_schema, dict) else {}
    item_type = item_schema.get("type")

    if item_type == "string" or (isinstance(item_type, list) and "string" in item_type):
        sanitized: list[str] = []
        for item in sources:
            if isinstance(item, str):
                m = re.match(r"\[(.*?)\]\((.*?)\)", item.strip())
                if m:
                    title = m.group(1).strip()
                    url = m.group(2).strip()
                    combined = ": ".join(filter(None, [title, url]))
                    if combined:
                        sanitized.append(combined)
                else:
                    val = item.strip()
                    if val:
                        sanitized.append(val)
            elif isinstance(item, dict):
                title = (item.get("title") or "").strip()
                url = (item.get("url") or "").strip()
                if title or url:
                    if title and url:
                        sanitized.append(f"{title}: {url}")
                    else:
                        sanitized.append(title or url)
        new = dict(data)
        new["sources"] = sanitized
        return new

    if item_type == "object" or (isinstance(item_type, list) and "object" in item_type):
        sanitized_objs: list[dict[str, Any]] = []
        for item in sources:
            if isinstance(item, dict):
                title = (item.get("title") or item.get("url") or "").strip()
                sid = (item.get("id") or item.get("url") or _slugify(title)).strip()
                url = (item.get("url") or "").strip()
                if not sid and url:
                    sid = url
                if not title and url:
                    title = url
                if sid and title:
                    entry = {"id": sid, "title": title}
                    if url:
                        entry["url"] = url
                    sanitized_objs.append(entry)
            elif isinstance(item, str):
                m = re.match(r"\[(.*?)\]\((.*?)\)", item.strip())
                if m:
                    title = m.group(1).strip()
                    url = m.group(2).strip()
                    sid = _slugify(title) or url
                    entry = {"id": sid or url or title or "", "title": title or url or ""}
                    if url:
                        entry["url"] = url
                    sanitized_objs.append(entry)
                else:
                    url = item.strip()
                    if url:
                        entry = {"id": url, "title": url}
                        entry["url"] = url
                        sanitized_objs.append(entry)
        new = dict(data)
        new["sources"] = sanitized_objs
        return new

    return data


def clean_json_payload(data: dict, schema: dict) -> dict:
    """Return *data* normalized against *schema* before validation.

    - Unknown keys are stripped when ``additionalProperties`` is ``false``.
    - ``sources`` entries are sanitized for both string and object modes.
    - Bullet points and multiline strings are collapsed into semicolon separated
      strings.
    - Array fields accept single strings split on semicolons or newlines.
    - Missing required fields are filled with defaults via ``make_empty_payload``.
    """

    from core.agents.prompt_agent import (
        strip_additional_properties,
        make_empty_payload,
        coerce_types,
    )

    if not isinstance(data, dict):
        data = {}

    if (schema.get("properties") or {}).get("sources") is not None:
        data = sanitize_sources(data, schema)
    data = strip_additional_properties(data, schema)

    def _strip_bullet(text: str) -> str:
        return re.sub(r"^[\s]*[-*]\s*", "", text).strip()

    def _normalize(obj: Any, sch: dict) -> Any:
        if not isinstance(sch, dict):
            return obj
        t = sch.get("type")
        if isinstance(t, list):
            if "object" in t:
                t = "object"
            elif "array" in t:
                t = "array"
            elif "string" in t:
                t = "string"
        if t == "object":
            if isinstance(obj, dict):
                props = sch.get("properties", {}) or {}
                return {k: _normalize(v, props.get(k, {})) for k, v in obj.items() if k in props}
            return {}
        if t == "array":
            item_schema = sch.get("items", {}) or {}
            item_type = item_schema.get("type")
            if isinstance(item_type, list) and "string" in item_type:
                item_type = "string"
            if item_type == "string":
                if isinstance(obj, str):
                    parts = re.split(r"[\n;]+", obj)
                    return [p for p in (_strip_bullet(x) for x in parts) if p]
                if isinstance(obj, list):
                    return [p for p in (_strip_bullet(str(x)) for x in obj if isinstance(x, str)) if p]
                return []
            if isinstance(obj, list):
                return [_normalize(x, item_schema) for x in obj]
            return []
        if t == "string":
            if isinstance(obj, list):
                items = [p for p in (_strip_bullet(str(x)) for x in obj if isinstance(x, str)) if p]
                return "; ".join(items)
            if isinstance(obj, str):
                parts = re.split(r"[\n;]+", obj)
                items = [p for p in (_strip_bullet(x) for x in parts) if p]
                return "; ".join(items)
            return obj if isinstance(obj, str) else ""
        return obj

    data = _normalize(data, schema)

    placeholder = make_empty_payload(schema)
    placeholder.update(data)
    data = strip_additional_properties(placeholder, schema)
    data = coerce_types(data, schema)
    return data
