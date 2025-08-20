from typing import Any, Union, List
import json


def coerce_user_content(x: Any) -> Union[str, List[dict]]:
    """
    OpenAI chat messages must be str or list[dict] (for vision).
    - str: return as-is
    - list[dict]: assume vision content; return as-is
    - dict/other: JSON-dump to a compact string
    """
    if isinstance(x, str):
        return x
    if isinstance(x, list) and all(isinstance(i, dict) for i in x):
        return x
    try:
        return json.dumps(x, separators=(",", ":"), ensure_ascii=False)
    except Exception:
        return str(x)
