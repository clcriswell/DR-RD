from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List
import yaml

from .schemas import ComplianceProfile, ComplianceReport

ROOT = Path(__file__).resolve().parent


def load_profile(profile_id: str) -> ComplianceProfile:
    fp = ROOT / "profiles" / f"{profile_id}.yaml"
    data = yaml.safe_load(fp.read_text())
    return ComplianceProfile(**data)


def _extract_claims(text: str) -> List[Dict[str, str]]:
    sentences = [s.strip() for s in re.split(r"[\.\n]", text) if s.strip()]
    return [{"id": f"c{i+1}", "text": s} for i, s in enumerate(sentences)]


def check(text: str, profile: ComplianceProfile, context: Dict) -> ComplianceReport:
    claims = _extract_claims(text)
    unmet: List[str] = []
    for item in profile.items:
        if item.tag and item.tag.lower() in text.lower():
            continue
        if not item.required:
            continue
        unmet.append(item.id)
    coverage = (len(profile.items) - len(unmet)) / max(len(profile.items), 1)
    report = ComplianceReport(
        coverage=coverage,
        unmet=unmet,
        citations=[],
        notes={"claims": claims},
    )
    return report
