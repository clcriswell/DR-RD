import json
import re
from .json_safety import parse_json_loose


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
