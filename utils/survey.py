"""Survey scoring utilities."""
from __future__ import annotations

from typing import Dict

SUS_ITEMS: Dict[str, str] = {
    "sus_q1": "I think that I would like to use this system frequently.",
    "sus_q2": "I found the system unnecessarily complex.",
    "sus_q3": "I thought the system was easy to use.",
    "sus_q4": "I think that I would need the support of a technical person to be able to use this system.",
    "sus_q5": "I found the various functions in this system were well integrated.",
    "sus_q6": "I thought there was too much inconsistency in this system.",
    "sus_q7": "I would imagine that most people would learn to use this system very quickly.",
    "sus_q8": "I found the system very cumbersome to use.",
    "sus_q9": "I felt very confident using the system.",
    "sus_q10": "I needed to learn a lot of things before I could get going with this system.",
}


def validate_sus(responses: Dict[str, int]) -> None:
    """Validate that all 10 SUS items are present with scores 1-5."""
    if set(responses) != set(SUS_ITEMS):
        raise ValueError("SUS responses must include all 10 items")
    if any(not 1 <= v <= 5 for v in responses.values()):
        raise ValueError("SUS responses must be between 1 and 5")


def score_sus(responses: Dict[str, int]) -> int:
    """Convert SUS item scores from 1-5 Likert to a 0-100 total."""
    validate_sus(responses)
    total = 0
    for idx, key in enumerate(sorted(SUS_ITEMS.keys(), key=lambda k: int(k.split('q')[1])), start=1):
        score = responses[key]
        if idx % 2 == 1:  # odd items
            total += score - 1
        else:  # even items
            total += 5 - score
    return int(total * 2.5)


def normalize_seq(score: int) -> int:
    """Clamp SEQ score to 1-7 Likert scale."""
    return max(1, min(int(score), 7))
