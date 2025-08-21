import json
import re

from .json_safety import parse_json_loose


class AgentOutputFormatError(ValueError):
    """Raised when an agent returns malformed JSON that cannot be repaired."""


def extract_json_block(text: str):
    m = re.search(r"```json\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL | re.IGNORECASE)
    if not m:
        return None
    block = m.group(1)
    try:
        return json.loads(block)
    except Exception:
        try:
            return parse_json_loose(block)
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
