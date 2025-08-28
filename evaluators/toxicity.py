from __future__ import annotations

from dr_rd.safety import filters


def evaluate(text: str) -> bool:
    score = filters.detect_toxicity(text)
    return score <= filters.SAFETY_CFG.get("toxicity_threshold", 1.0)
