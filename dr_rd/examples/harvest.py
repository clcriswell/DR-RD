from __future__ import annotations

from typing import Dict, List

from dr_rd.kb.models import KBRecord

EXAMPLE_MIN_SCORE = 0.7


def harvest(records: List[KBRecord]) -> List[Dict]:
    examples: List[Dict] = []
    for rec in records:
        if not rec.sources:
            continue
        if rec.metrics.get("evaluator_ok") is False:
            continue
        if rec.metrics.get("repair_rate", 0.0) > 0.3:
            continue
        score = float(rec.metrics.get("quality_score", 1.0))
        if score < EXAMPLE_MIN_SCORE:
            continue
        examples.append(
            {
                "role": rec.agent_role,
                "task_signature": rec.task_title,
                "inputs_signature": str(sorted(rec.inputs.items())),
                "output_snippet": str(rec.output_json)[:120],
                "sources_meta": [s.meta for s in rec.sources],
                "quality_score": score,
                "ts": rec.ts,
            }
        )
    return examples
