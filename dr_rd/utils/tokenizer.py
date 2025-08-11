from typing import List, Dict


def estimate(messages: List[Dict[str, str]]) -> int:
    """Rough token estimate based on whitespace splitting."""
    if not messages:
        return 0
    total = 0
    for m in messages:
        text = m.get("content", "")
        total += len(str(text).split())
    return total
