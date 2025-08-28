"""Source quality scoring heuristics."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import yaml

from .types import Doc

CFG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "rag.yaml"
CFG = yaml.safe_load(CFG_PATH.read_text()) if CFG_PATH.exists() else {}
REP_PATH = Path(CFG.get("domain_reputation_file", "dr_rd/rag/domain_reputation.yaml"))
REP_DATA = yaml.safe_load(REP_PATH.read_text()) if REP_PATH.exists() else {}
DOMAIN_WEIGHTS: Dict[str, float] = REP_DATA.get("domains", {})
BLOCKED = set(REP_DATA.get("blocked_domains", []))


def score_source(doc: Doc, query: str, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    if any(b in doc.url for b in BLOCKED):
        return 0.0
    domain_w = DOMAIN_WEIGHTS.get(doc.domain, 0.5)
    recency = 1.0
    if doc.published_at:
        try:
            dt = datetime.fromisoformat(doc.published_at.replace("Z", "+00:00"))
            days = (now - dt).days
            recency = max(0.0, 1.0 - days / 365.0)
        except Exception:
            pass
    q_tokens = set(query.lower().split())
    text_tokens = set(doc.text.lower().split())
    coverage = len(q_tokens & text_tokens) / max(len(q_tokens), 1)
    length_factor = min(len(doc.text) / 1000.0, 1.0)
    score = domain_w * 0.6 + recency * 0.3 + coverage * 0.05 + length_factor * 0.05
    return max(min(score, 1.0), 0.0)
