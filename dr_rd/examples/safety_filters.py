from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

import yaml

POLICY_PATH = Path(__file__).with_name("policies.yaml")

_email_re = re.compile(r"\b[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}\b")
_phone_re = re.compile(r"\b\d{3}-\d{3}-\d{4}\b")
_secret_re = re.compile(r"sk-[A-Za-z0-9]{10,}")


def load_policies() -> Dict:
    with open(POLICY_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _contains(block: List[str] | None, text: str) -> bool:
    return any(b in text for b in block or [])


def filter_and_redact(cands: List[Dict], policies: Dict) -> List[Dict]:
    block = policies.get("blocklist", {})
    allow_domains = set(policies.get("allow_domains", []))
    out: List[Dict] = []
    for c in cands:
        blob = json.dumps(c, ensure_ascii=False)
        if _email_re.search(blob) or _phone_re.search(blob) or _secret_re.search(blob):
            continue
        if _contains(block.get("pii"), blob) or _contains(block.get("secrets"), blob) or _contains(block.get("copyright"), blob):
            continue
        if allow_domains:
            def repl(m: re.Match) -> str:
                host = m.group(1)
                return m.group(0) if host in allow_domains else "[REDACTED]"
            blob = re.sub(r"https?://([^\"\s/]+)", repl, blob)
            c = json.loads(blob)
        # ensure output is valid JSON if present
        try:
            json.loads(json.dumps(c.get("output", {})))
        except Exception:
            continue
        out.append(c)
    return out
