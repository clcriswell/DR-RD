from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

from dr_rd.policy.engine import PolicyDecision, load_policies, evaluate as policy_evaluate

CFG_PATH = Path("config/safety.yaml")
SAFETY_CFG: Dict[str, Any] = yaml.safe_load(CFG_PATH.read_text()) if CFG_PATH.exists() else {}

PII_PATTERNS = {
    name: re.compile(pattern, re.IGNORECASE)
    for name, pattern in SAFETY_CFG.get("pii_patterns", {}).items()
}
SECRETS_PATTERNS = {
    name: re.compile(pattern, re.IGNORECASE)
    for name, pattern in SAFETY_CFG.get("secrets_patterns", {}).items()
}
TOXICITY_THRESHOLD = float(SAFETY_CFG.get("toxicity_threshold", 1.0))
BLOCKED_KEYWORDS = [w.lower() for w in SAFETY_CFG.get("blocked_keywords", [])]
ALLOWED_DOMAINS = SAFETY_CFG.get("allowed_link_domains", [])
LICENSE_MAX_QUOTE_WORDS = int(SAFETY_CFG.get("license_max_quote_words", 0))


def detect_pii(text: str) -> Dict[str, str]:
    matches: Dict[str, str] = {}
    for name, pat in PII_PATTERNS.items():
        m = pat.search(text)
        if m:
            matches[name] = m.group(0)
    return matches


def detect_secrets(text: str) -> Dict[str, str]:
    matches: Dict[str, str] = {}
    for name, pat in SECRETS_PATTERNS.items():
        m = pat.search(text)
        if m:
            matches[name] = m.group(0)
    return matches


def detect_toxicity(text: str) -> float:
    if not text.strip():
        return 0.0
    tokens = re.findall(r"\w+", text.lower())
    toxic = sum(1 for t in tokens if t in BLOCKED_KEYWORDS)
    return toxic / max(len(tokens), 1)


def enforce_license(text: str) -> Dict[str, str]:
    violations: Dict[str, str] = {}
    # quote length check
    for quote in re.findall(r"\"([^\"]+)\"", text):
        words = quote.split()
        if LICENSE_MAX_QUOTE_WORDS and len(words) > LICENSE_MAX_QUOTE_WORDS:
            violations["quote"] = quote
            break
    # link domain check
    for url in re.findall(r"https?://([^/\s]+)", text):
        if ALLOWED_DOMAINS and not any(url.endswith(d) for d in ALLOWED_DOMAINS):
            violations["link"] = url
            break
    for w in BLOCKED_KEYWORDS:
        if w in text.lower():
            violations["keyword"] = w
            break
    return violations


def redact(text: str, matches: Dict[str, str]) -> str:
    redacted = text
    for name, value in matches.items():
        redacted = re.sub(re.escape(value), f"[REDACTED:{name}]", redacted)
    return redacted


def _walk(obj: Any) -> Tuple[Any, Dict[str, str]]:
    matches: Dict[str, str] = {}
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            new_v, m = _walk(v)
            matches.update(m)
            new_dict[k] = new_v
        return new_dict, matches
    if isinstance(obj, list):
        new_list = []
        for item in obj:
            new_item, m = _walk(item)
            matches.update(m)
            new_list.append(new_item)
        return new_list, matches
    if isinstance(obj, str):
        pii = detect_pii(obj)
        secrets = detect_secrets(obj)
        to_redact = {**pii, **secrets}
        if to_redact:
            obj = redact(obj, to_redact)
            matches.update({f"pii:{k}": v for k, v in pii.items()})
            matches.update({f"secrets:{k}": v for k, v in secrets.items()})
        tox = detect_toxicity(obj)
        if tox > TOXICITY_THRESHOLD:
            matches["toxicity"] = str(tox)
        lic = enforce_license(obj)
        for k, v in lic.items():
            matches[f"license:{k}"] = v
        return obj, matches
    return obj, matches


def filter_output(json_obj: Any) -> Tuple[Any, PolicyDecision]:
    sanitized, matches = _walk(json_obj)
    decision = policy_evaluate(json_obj)
    if matches:
        # apply redactions already applied; if policy says block, mark not allowed
        if any(k.startswith("secrets") for k in matches.keys()):
            if "secrets" in decision.violations or "secrets" in decision.redactions:
                pass
        if decision.violations:
            decision.allowed = False
    return sanitized, decision
