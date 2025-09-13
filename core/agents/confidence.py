from __future__ import annotations

"""Utilities for handling agent confidence values."""

from typing import Union, Optional

# Mapping of descriptive terms to normalized numeric scores.
CONFIDENCE_MAP = {
    "high": 0.9,
    "moderate": 0.6,
    "medium": 0.6,
    "low": 0.3,
}


def normalize_confidence(value: Optional[Union[str, int, float]]) -> Optional[Union[int, float]]:
    """Return a numeric confidence value.

    Descriptive strings are mapped to floats in the range [0,1]. Numeric
    inputs are returned unchanged to preserve backward compatibility.
    Unknown strings fall back to a neutral 0.5 score.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        key = value.strip().lower()
        for phrase, score in CONFIDENCE_MAP.items():
            if phrase in key:
                return score
        return 0.5
    return None
