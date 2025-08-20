from __future__ import annotations

"""Helpers for scoring text against an LLM-provided rubric."""

import json
import os
from typing import Any, Dict


def _clip(x: float) -> float:
    """Clip ``x`` into the inclusive range [0.0, 1.0]."""

    return max(0.0, min(1.0, float(x)))


def workspace_to_text(workspace: Any) -> str:
    """Return textual representation of a workspace for evaluation.

    The helper tries a few strategies in order:

    1. ``workspace.joined_results_text()`` if callable.
    2. Join ``workspace.results`` with double newlines.
    3. Fallback to ``str(workspace)``.
    """

    if hasattr(workspace, "joined_results_text") and callable(
        getattr(workspace, "joined_results_text")
    ):
        try:
            return str(workspace.joined_results_text())
        except Exception:
            pass

    if hasattr(workspace, "results"):
        try:
            iterable = getattr(workspace, "results")
            return "\n\n".join(map(str, iterable))
        except Exception:
            pass

    return str(workspace)


def score_with_rubric(text: str, rubric: str) -> float:
    """Score ``text`` against ``rubric`` using the configured LLM.

    The function attempts to obtain a JSON response like ``{"score": 0.5, ...}``
    from either an internal ``dr_rd.llm`` client or the OpenAI API. Any errors
    or malformed responses result in a score of ``0.0``. The final score is
    clipped to the range [0.0, 1.0].
    """

    prompt = (
        "You are an impartial evaluator.\n"
        "Return STRICT JSON with keys: score (float 0..1) and rationale (string).\n"
        "Do not include any extra commentary.\n\n"
        f"RUBRIC:\n{rubric}\n\n"
        "TEXT TO EVALUATE:\n"
        f"{text}\n"
    )

    # Prefer an internal helper if available.
    try:  # pragma: no cover - exercised via monkeypatch in tests
        from dr_rd.llm import chat_json  # type: ignore

        try:
            resp = chat_json(prompt)
            score = float(resp.get("score", 0.0))
            return _clip(score)
        except Exception:
            pass
    except Exception:
        pass

    # Fallback to OpenAI; tests monkeypatch this function so no network call.
    try:  # pragma: no cover - network not exercised in tests
        from dr_rd.llm_client import call_openai

        model = (
            os.getenv("DRRD_LLM_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "gpt-5"
        )

        result = call_openai(
            model=model,
            messages=[
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = result["text"] or "{}"
        data: Dict[str, Any] = json.loads(content or "{}")
        score = float(data.get("score", 0.0))
        return _clip(score)
    except Exception:
        return 0.0


__all__ = ["score_with_rubric", "workspace_to_text"]

