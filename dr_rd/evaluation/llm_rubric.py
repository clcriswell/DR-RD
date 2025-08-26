"""Lightweight helpers for rubric-based scoring.

The real system may call out to an LLM. For tests we provide a deterministic
fallback that hashes the text and rubric keys into scores in ``[0,1]``.
"""
from __future__ import annotations

import hashlib
from typing import Dict

import config.feature_flags as ff


def _det_score(text: str, key: str) -> float:
    data = (text + key).encode("utf-8")
    h = hashlib.sha256(data).hexdigest()
    return (int(h, 16) % 100) / 100.0


def score_with_rubric(text: str, rubric: Dict[str, str]) -> Dict[str, float]:
    """Return scores for each rubric key.

    Network calls are gated behind ``EVALUATORS_ENABLED``. If disabled, zeros
    are returned for each metric. In this repo we always fall back to a
    deterministic hash-based score which keeps the function pure and bounded.
    """
    if not ff.EVALUATORS_ENABLED:
        return {k: 0.0 for k in rubric}

    scores: Dict[str, float] = {}
    for key in rubric:
        try:
            scores[key] = _det_score(text, key)
        except Exception:
            scores[key] = 0.0
    return scores


__all__ = ["score_with_rubric"]
