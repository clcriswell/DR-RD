"""Quality assurance helper functions."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List


def build_requirements_matrix(reqs: List[str], tests: List[str]) -> Dict[str, List[str]]:
    """Map each requirement to the tests that mention it."""
    matrix: Dict[str, List[str]] = {}
    for r in reqs:
        r_l = r.lower()
        matrix[r] = [t for t in tests if r_l in t.lower()]
    return matrix


def compute_test_coverage(matrix: Dict[str, List[str]]) -> Dict:
    """Compute coverage stats from a requirements matrix."""
    total = len(matrix)
    covered = [r for r, ts in matrix.items() if ts]
    uncovered = [r for r, ts in matrix.items() if not ts]
    coverage = len(covered) / total if total else 0.0
    return {"total": total, "covered": covered, "uncovered": uncovered, "coverage": coverage}


def classify_defects(defects: List[Dict]) -> Dict[str, List[Dict]]:
    """Bucket defects by severity."""
    buckets: Dict[str, List[Dict]] = defaultdict(list)
    for d in defects:
        sev = (d.get("severity") or "minor").lower()
        if sev not in {"critical", "major", "minor"}:
            sev = "minor"
        buckets[sev].append(d)
    return {k: buckets.get(k, []) for k in ("critical", "major", "minor")}
