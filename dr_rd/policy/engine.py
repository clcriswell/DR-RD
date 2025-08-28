from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Set, Any

import yaml

POLICY_PATH = Path(__file__).resolve().parent / "policies.yaml"


def load_policies() -> Dict[str, Dict[str, str]]:
    """Load policy configuration from ``policies.yaml``."""
    data = yaml.safe_load(POLICY_PATH.read_text())
    return data or {}


@dataclass
class PolicyDecision:
    allowed: bool
    redactions: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def classify(payload: Any) -> Set[str]:
    """Classify text or JSON payload into policy classes.

    This lightweight implementation delegates to safety filters for detection.
    """
    from dr_rd.safety import filters  # local import to avoid cycles

    text = payload
    if isinstance(payload, (dict, list)):
        text = json.dumps(payload)
    classes: Set[str] = set()
    if filters.detect_pii(str(text)):
        classes.add("pii")
    if filters.detect_secrets(str(text)):
        classes.add("secrets")
    if filters.detect_toxicity(str(text)) > filters.SAFETY_CFG.get("toxicity_threshold", 1.0):
        classes.add("toxicity")
    if filters.enforce_license(str(text)):
        classes.add("license")
    return classes


def decide(classes: Iterable[str]) -> Dict[str, str]:
    """Resolve final actions for policy classes."""
    policies = load_policies()
    return {c: policies.get(c, {}).get("action", "allow") for c in classes}


def evaluate(payload: Any) -> PolicyDecision:
    classes = classify(payload)
    actions = decide(classes)
    policies = load_policies()
    allowed = True
    redactions: List[str] = []
    violations: List[str] = []
    notes: List[str] = []
    for c in classes:
        action = actions.get(c, "allow")
        note = policies.get(c, {}).get("notes")
        if note:
            notes.append(note)
        if action == "block":
            allowed = False
            violations.append(c)
        elif action == "redact":
            redactions.append(c)
    return PolicyDecision(allowed=allowed, redactions=redactions, violations=violations, notes=notes)
