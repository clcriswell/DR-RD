from __future__ import annotations

"""Scoring helpers for evaluation runs."""

from typing import Any, Dict, List
import os
import re
from utils import llm_client


_keyword_re = re.compile(r"\b\w+\b")


def _word_count(text: str) -> int:
    return len(_keyword_re.findall(text))


def score_with_llm(text: str, rubric: str, *, mode: str, budget_ms: int = 1200) -> float | None:
    if os.getenv("NO_NET") == "1":
        return None
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "Score the text 0..1 according to the rubric. Reply with a float only.",
            },
            {
                "role": "user",
                "content": f"Rubric:\n{rubric}\n\nText:\n{text}\nScore:",
            },
        ]
    }
    try:
        resp = llm_client.chat(payload, mode=mode, cache_ttl_sec=0)
        content = resp["choices"][0]["message"]["content"].strip()
        return max(0.0, min(1.0, float(content)))
    except Exception:
        return None


def score_item(output_text: str, meta: Dict[str, Any], spec: Dict[str, Any], *, use_llm: bool = False) -> Dict[str, Any]:
    txt = output_text or ""
    flags: List[str] = []
    exp = [k.lower() for k in spec.get("expected_keywords", [])]
    forb = [k.lower() for k in spec.get("forbidden_keywords", [])]
    lower = txt.lower()
    coverage = 1.0
    if exp:
        found = sum(1 for k in exp if k in lower)
        coverage = found / len(exp)
    heuristic = coverage
    if any(k in lower for k in forb):
        heuristic = 0.0
        flags.append("forbidden")
    wc = _word_count(txt)
    if spec.get("min_words") and wc < int(spec["min_words"]):
        heuristic = 0.0
        flags.append("too_short")
    if spec.get("max_words") and wc > int(spec["max_words"]):
        heuristic = 0.0
        flags.append("too_long")
    if meta.get("status") != "success":
        heuristic = 0.0
        flags.append("error")
    llm_score = None
    if use_llm and spec.get("rubric"):
        llm_score = score_with_llm(txt, spec["rubric"], mode=spec.get("mode", "standard"))
    if llm_score is not None:
        final = (heuristic + llm_score) / 2
    else:
        final = heuristic
    return {
        "id": spec.get("id"),
        "heuristic": round(heuristic, 3),
        "llm": llm_score,
        "final": round(final, 3),
        "flags": flags,
    }
